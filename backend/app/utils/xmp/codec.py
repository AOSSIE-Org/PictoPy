import base64
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Protocol, Tuple

import numpy as np

from app.logging.setup_logging import get_logger

from .containers.base import MAX_PACKET_BYTES
from .schema import (
    SCHEMA_VERSION,
    EmbeddingRecord,
    FaceRecord,
    PictoPyMetadata,
    SemanticTag,
)

logger = get_logger(__name__)

NS_RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
NS_X = "adobe:ns:meta/"
NS_PICTOPY = "https://pictopy.app/ns/1.0/"

# Keeps other tools' prefixes stable when we re-serialize their packet.
for _prefix, _uri in {
    "x": NS_X,
    "rdf": NS_RDF,
    "pictopy": NS_PICTOPY,
    "dc": "http://purl.org/dc/elements/1.1/",
    "xmp": "http://ns.adobe.com/xap/1.0/",
    "xmpMM": "http://ns.adobe.com/xap/1.0/mm/",
    "exif": "http://ns.adobe.com/exif/1.0/",
    "tiff": "http://ns.adobe.com/tiff/1.0/",
    "photoshop": "http://ns.adobe.com/photoshop/1.0/",
}.items():
    ET.register_namespace(_prefix, _uri)

_XPACKET_BEGIN = '<?xpacket begin="﻿" id="W5M0MpCehiHzreSzNTczkc9d"?>'
_XPACKET_END = '<?xpacket end="w"?>'


class NewerSchemaError(ValueError):
    """The image holds PictoPy data from a newer version; overwriting would lose it."""


@dataclass
class PacketHeader:
    schema_version: int
    digest: Optional[str]


def _q(ns: str, name: str) -> str:
    return f"{{{ns}}}{name}"


class XmpCodec(Protocol):
    """Turns metadata into a packet and back; swap to change the representation."""

    def encode(
        self, metadata: PictoPyMetadata, existing: Optional[bytes] = None
    ) -> bytes: ...

    def decode(self, packet: bytes) -> Optional[PictoPyMetadata]: ...

    def digest(self, metadata: PictoPyMetadata) -> str: ...

    def read_header(self, packet: bytes) -> Optional[PacketHeader]: ...

    def strip(self, packet: bytes) -> Optional[bytes]: ...

    # Byte strings at least one of which any packet holding this codec's
    # data must contain, however it is spelled or encoded.
    markers: Tuple[bytes, ...]


def _vec_to_text(vec: List[float]) -> str:
    return base64.b64encode(np.asarray(vec, dtype="<f4").tobytes()).decode("ascii")


def _text_to_vec(text: str) -> List[float]:
    return np.frombuffer(base64.b64decode(text, validate=True), dtype="<f4").tolist()


def _text_of(parent: ET.Element, name: str) -> Optional[str]:
    """A simple property, in element or attribute form (exiftool writes the latter)."""
    node = parent.find(_q(NS_PICTOPY, name))
    if node is not None:
        return node.text
    return parent.get(_q(NS_PICTOPY, name))


def _add(parent: ET.Element, name: str, text: str) -> None:
    ET.SubElement(parent, _q(NS_PICTOPY, name)).text = text


def _list_items(parent: ET.Element, name: str, container: str) -> List[ET.Element]:
    """The rdf:li items of a pictopy Bag/Seq property."""
    return parent.findall(
        f"{_q(NS_PICTOPY, name)}/{_q(NS_RDF, container)}/{_q(NS_RDF, 'li')}"
    )


def _new_list(parent: ET.Element, name: str, container: str) -> ET.Element:
    prop = ET.SubElement(parent, _q(NS_PICTOPY, name))
    return ET.SubElement(prop, _q(NS_RDF, container))


def _new_struct(lst: ET.Element) -> ET.Element:
    li = ET.SubElement(lst, _q(NS_RDF, "li"))
    return ET.SubElement(li, _q(NS_RDF, "Description"))


def _structs(parent: ET.Element, name: str, container: str) -> List[ET.Element]:
    return [
        desc
        for li in _list_items(parent, name, container)
        if (desc := li.find(_q(NS_RDF, "Description"))) is not None
    ]


def _encode_bag(parent: ET.Element, name: str, items: List[str]) -> None:
    if not items:
        return
    bag = _new_list(parent, name, "Bag")
    for item in items:
        ET.SubElement(bag, _q(NS_RDF, "li")).text = item


def _decode_bag(parent: ET.Element, name: str) -> List[str]:
    return [li.text or "" for li in _list_items(parent, name, "Bag")]


# Sections: one encode/decode pair per field, so each can change on its own.
_Encode = Callable[[PictoPyMetadata, ET.Element], None]
_Decode = Callable[[ET.Element, PictoPyMetadata], None]


def _enc_tags(m: PictoPyMetadata, p: ET.Element) -> None:
    _encode_bag(p, "Tags", m.tags)


def _dec_tags(p: ET.Element, m: PictoPyMetadata) -> None:
    m.tags = _decode_bag(p, "Tags")


def _enc_semantic(m: PictoPyMetadata, p: ET.Element) -> None:
    if not m.semantic_tags:
        return
    bag = _new_list(p, "SemanticTags", "Bag")
    for tag in m.semantic_tags:
        item = _new_struct(bag)
        _add(item, "Name", tag.name)
        _add(item, "Score", repr(float(tag.score)))


def _dec_semantic(p: ET.Element, m: PictoPyMetadata) -> None:
    for item in _structs(p, "SemanticTags", "Bag"):
        name, score = _text_of(item, "Name"), _text_of(item, "Score")
        if name and score:
            m.semantic_tags.append(SemanticTag(name, float(score)))


def _enc_albums(m: PictoPyMetadata, p: ET.Element) -> None:
    _encode_bag(p, "Albums", m.albums)


def _dec_albums(p: ET.Element, m: PictoPyMetadata) -> None:
    m.albums = _decode_bag(p, "Albums")


def _enc_favourite(m: PictoPyMetadata, p: ET.Element) -> None:
    if m.favourite is not None:
        _add(p, "Favourite", str(m.favourite).lower())


def _dec_favourite(p: ET.Element, m: PictoPyMetadata) -> None:
    text = _text_of(p, "Favourite")
    if text is not None:
        m.favourite = text.strip().lower() == "true"


def _enc_faces(m: PictoPyMetadata, p: ET.Element) -> None:
    if not m.faces:
        return
    seq = _new_list(p, "Faces", "Seq")
    for face in m.faces:
        item = _new_struct(seq)
        _add(item, "Embedding", _vec_to_text(face.embedding))
        if face.bbox is not None:
            _add(item, "BBox", json.dumps(face.bbox, sort_keys=True))
        if face.confidence is not None:
            _add(item, "Confidence", repr(float(face.confidence)))
        if face.cluster_name:
            _add(item, "ClusterName", face.cluster_name)


def _dec_faces(p: ET.Element, m: PictoPyMetadata) -> None:
    for item in _structs(p, "Faces", "Seq"):
        embedding = _text_of(item, "Embedding")
        if not embedding:
            continue
        bbox = _text_of(item, "BBox")
        conf = _text_of(item, "Confidence")
        m.faces.append(
            FaceRecord(
                embedding=_text_to_vec(embedding),
                bbox=json.loads(bbox) if bbox else None,
                confidence=float(conf) if conf else None,
                cluster_name=_text_of(item, "ClusterName"),
            )
        )


def _enc_embedding(m: PictoPyMetadata, p: ET.Element) -> None:
    if m.image_embedding is None:
        return
    prop = ET.SubElement(p, _q(NS_PICTOPY, "ImageEmbedding"))
    desc = ET.SubElement(prop, _q(NS_RDF, "Description"))
    _add(desc, "ModelVersion", m.image_embedding.model_version)
    _add(desc, "Vector", _vec_to_text(m.image_embedding.vector))


def _dec_embedding(p: ET.Element, m: PictoPyMetadata) -> None:
    desc = p.find(f"{_q(NS_PICTOPY, 'ImageEmbedding')}/{_q(NS_RDF, 'Description')}")
    if desc is None:
        return
    version, vector = _text_of(desc, "ModelVersion"), _text_of(desc, "Vector")
    if version and vector:
        m.image_embedding = EmbeddingRecord(version, _text_to_vec(vector))


def _enc_models(m: PictoPyMetadata, p: ET.Element) -> None:
    if not m.models:
        return
    bag = _new_list(p, "Models", "Bag")
    for role in sorted(m.models):
        item = _new_struct(bag)
        _add(item, "Role", role)
        _add(item, "Version", m.models[role])


def _dec_models(p: ET.Element, m: PictoPyMetadata) -> None:
    models: Dict[str, str] = {}
    for item in _structs(p, "Models", "Bag"):
        role, version = _text_of(item, "Role"), _text_of(item, "Version")
        if role and version:
            models[role] = version
    m.models = models


def _enc_dimensions(m: PictoPyMetadata, p: ET.Element) -> None:
    if m.width is not None and m.height is not None:
        _add(p, "Width", str(m.width))
        _add(p, "Height", str(m.height))


def _dec_dimensions(p: ET.Element, m: PictoPyMetadata) -> None:
    width, height = _text_of(p, "Width"), _text_of(p, "Height")
    if width and height:
        m.width, m.height = int(width), int(height)


# Add a section here to export a new kind of data; nothing else needs to change.
SECTIONS: List[Tuple[str, _Encode, _Decode]] = [
    ("tags", _enc_tags, _dec_tags),
    ("semantic_tags", _enc_semantic, _dec_semantic),
    ("faces", _enc_faces, _dec_faces),
    ("image_embedding", _enc_embedding, _dec_embedding),
    ("favourite", _enc_favourite, _dec_favourite),
    ("albums", _enc_albums, _dec_albums),
    ("models", _enc_models, _dec_models),
    ("dimensions", _enc_dimensions, _dec_dimensions),
]


def _parse(packet: bytes) -> ET.Element:
    if len(packet) > MAX_PACKET_BYTES:
        raise ValueError("XMP packet too large")
    # XMP never needs a DTD; refusing it closes entity-expansion attacks, since
    # the packet comes from a file we did not necessarily write.
    upper = packet.upper()
    if b"<!DOCTYPE" in upper or b"<!ENTITY" in upper:
        raise ValueError("XMP packet declares a DTD")
    return ET.fromstring(packet)


_CHAR_REF = re.compile(rb"&#(x[0-9a-fA-F]+|[0-9]+);")
_NS_BYTES = NS_PICTOPY.encode("utf-8")


def _resolve_char_ref(match: "re.Match[bytes]") -> bytes:
    ref = match.group(1)
    try:
        code = int(ref[1:], 16) if ref.startswith(b"x") else int(ref)
        return chr(code).encode("utf-8")
    except (ValueError, OverflowError):
        # Not a real character, so it cannot spell one of ours.
        return match.group(0)


def _may_hold_pictopy(packet: bytes) -> bool:
    """For a packet that cannot be parsed: could it spell our namespace?

    Besides literally, XML can spell a namespace only with numeric character
    references, declared entities, or in UTF-16/32. References are resolved;
    the other two never occur in real PNG XMP, so they count as "maybe".
    """
    # NUL is illegal in UTF-8 XML, so its presence means another encoding.
    if b"\x00" in packet or b"<!ENTITY" in packet:
        return True
    return _NS_BYTES in _CHAR_REF.sub(_resolve_char_ref, packet)


def _is_pictopy(qname: str) -> bool:
    return qname.startswith(f"{{{NS_PICTOPY}}}")


def _find_ours(root: ET.Element) -> Optional[ET.Element]:
    """The top-level description carrying our properties, if any."""
    for desc in root.iter(_q(NS_RDF, "Description")):
        if any(_is_pictopy(c.tag) for c in desc) or any(
            _is_pictopy(a) for a in desc.attrib
        ):
            return desc
    return None


def _header_of(desc: ET.Element) -> Optional[PacketHeader]:
    try:
        version = int(_text_of(desc, "SchemaVersion") or 0)
    except ValueError:
        return None
    return PacketHeader(version, _text_of(desc, "Digest"))


def _has_pictopy(root: ET.Element) -> bool:
    """Whether any element or attribute anywhere in the tree is ours."""
    return any(
        _is_pictopy(el.tag) or any(_is_pictopy(a) for a in el.attrib)
        for el in root.iter()
    )


def _rdf_of(root: ET.Element) -> Optional[ET.Element]:
    # The spec allows a bare rdf:RDF root as well as the usual x:xmpmeta wrapper.
    if root.tag == _q(NS_RDF, "RDF"):
        return root
    return root.find(_q(NS_RDF, "RDF"))


def _strip_ours(root: ET.Element) -> None:
    """Remove every pictopy element and attribute, at any depth.

    Other tools may share a description with us or, after editing the file,
    move our properties inside their own structures.
    """
    for parent in list(root.iter()):
        for child in [c for c in parent if _is_pictopy(c.tag)]:
            parent.remove(child)
        for attr in [a for a in parent.attrib if _is_pictopy(a)]:
            del parent.attrib[attr]
    rdf = _rdf_of(root)
    if rdf is None:
        return
    for desc in rdf.findall(_q(NS_RDF, "Description")):
        if len(desc) == 0 and set(desc.attrib) <= {_q(NS_RDF, "about")}:
            rdf.remove(desc)


class UnreadableXmpError(ValueError):
    """The image's existing XMP cannot be parsed; rewriting it would destroy it."""


def _xmpmeta_and_rdf(existing: Optional[bytes]) -> Tuple[ET.Element, ET.Element]:
    if not existing:
        root = ET.Element(_q(NS_X, "xmpmeta"))
        return root, ET.SubElement(root, _q(NS_RDF, "RDF"))
    try:
        root = _parse(existing)
    except (ET.ParseError, ValueError) as e:
        raise UnreadableXmpError(f"existing XMP unreadable: {e}") from e
    rdf = _rdf_of(root)
    if rdf is None:
        raise UnreadableXmpError("existing packet has no rdf:RDF")
    if root is rdf:
        wrapper = ET.Element(_q(NS_X, "xmpmeta"))
        wrapper.append(rdf)
        return wrapper, rdf
    return root, rdf


def _serialize(root: ET.Element) -> bytes:
    body = ET.tostring(root, encoding="unicode")
    return f"{_XPACKET_BEGIN}\n{body}\n{_XPACKET_END}".encode("utf-8")


def _build(metadata: PictoPyMetadata) -> Tuple[ET.Element, str]:
    """Our description plus the digest of its content, before the digest is added."""
    desc = ET.Element(_q(NS_RDF, "Description"))
    desc.set(_q(NS_RDF, "about"), "")
    _add(desc, "SchemaVersion", str(metadata.schema_version))
    for _name, enc, _dec in SECTIONS:
        enc(metadata, desc)
    # Hashing the encoded form means float32 rounding is identical on both
    # sides of a comparison, and vectors never need decoding to compare.
    digest = hashlib.sha256(ET.tostring(desc, encoding="utf-8")).hexdigest()
    return desc, digest


class PictoPyXmpCodec:
    """Stores PictoPy data as `pictopy:` properties in a standard XMP packet."""

    # For packets nobody can read, so nothing can be resolved: the namespace
    # or either way of spelling it differently, in every XMP encoding.
    markers = tuple(
        token.encode(encoding)
        for token in (NS_PICTOPY, "&#", "<!ENTITY")
        for encoding in ("utf-8", "utf-16-le", "utf-16-be", "utf-32-le", "utf-32-be")
    )

    def encode(
        self, metadata: PictoPyMetadata, existing: Optional[bytes] = None
    ) -> bytes:
        root, rdf = _xmpmeta_and_rdf(existing)
        current = _find_ours(rdf)
        header = _header_of(current) if current is not None else None
        if header is not None and header.schema_version > SCHEMA_VERSION:
            raise NewerSchemaError(
                f"packet has schema {header.schema_version}, we write {SCHEMA_VERSION}"
            )
        _strip_ours(root)

        ours, digest = _build(metadata)
        _add(ours, "Digest", digest)
        rdf.append(ours)
        return _serialize(root)

    def decode(self, packet: bytes) -> Optional[PictoPyMetadata]:
        try:
            ours = _find_ours(_parse(packet))
        except (ET.ParseError, ValueError) as e:
            logger.warning(f"Unreadable XMP packet: {e}")
            return None
        if ours is None:
            return None

        header = _header_of(ours)
        # Newer data may encode sections differently; do not guess.
        if header is None or not 1 <= header.schema_version <= SCHEMA_VERSION:
            return None

        metadata = PictoPyMetadata(schema_version=header.schema_version)
        for name, _enc, dec in SECTIONS:
            # One bad section must not discard the others.
            try:
                dec(ours, metadata)
            except Exception as e:
                logger.warning(f"Skipping malformed XMP section '{name}': {e}")
        return metadata

    def digest(self, metadata: PictoPyMetadata) -> str:
        return _build(metadata)[1]

    def read_header(self, packet: bytes) -> Optional[PacketHeader]:
        try:
            ours = _find_ours(_parse(packet))
        except (ET.ParseError, ValueError):
            return None
        return _header_of(ours) if ours is not None else None

    def strip(self, packet: bytes) -> Optional[bytes]:
        """The packet without PictoPy's data, or None if nothing else is left.

        Raises ValueError only when PictoPy data may be present but cannot be
        removed; callers must then drop the whole packet.
        """
        try:
            root = _parse(packet)
        except (ET.ParseError, ValueError) as e:
            # Unparseable, but our data cannot be expressed without our
            # namespace: if no spelling of it is present, it is theirs.
            if not _may_hold_pictopy(packet):
                return packet
            raise ValueError(f"unreadable XMP holding PictoPy data: {e}") from e
        if not _has_pictopy(root):
            # Nothing of ours: hand other tools' packet back byte-for-byte.
            return packet

        _strip_ours(root)
        if _has_pictopy(root):
            raise ValueError("PictoPy data survived stripping")
        rdf = _rdf_of(root)
        if len(rdf if rdf is not None else root) == 0:
            return None
        return _serialize(root)
