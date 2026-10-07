import base64
import json
import xml.etree.ElementTree as ET
from typing import Callable, List, Optional, Protocol, Tuple

import numpy as np

from app.logging.setup_logging import get_logger

from .schema import SCHEMA_VERSION, EmbeddingRecord, FaceRecord, PictoPyMetadata

logger = get_logger(__name__)

NS_RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
NS_X = "adobe:ns:meta/"
NS_PICTOPY = "https://pictopy.app/ns/1.0/"
# A packet this large is not something we wrote; refuse before parsing.
MAX_PACKET_BYTES = 64 * 1024 * 1024

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


def _q(ns: str, name: str) -> str:
    return f"{{{ns}}}{name}"


class XmpCodec(Protocol):
    """Turns metadata into a packet and back; swap to change the representation."""

    def encode(
        self, metadata: PictoPyMetadata, existing: Optional[bytes] = None
    ) -> bytes: ...

    def decode(self, packet: bytes) -> Optional[PictoPyMetadata]: ...


def _vec_to_text(vec: List[float]) -> str:
    return base64.b64encode(np.asarray(vec, dtype="<f4").tobytes()).decode("ascii")


def _text_to_vec(text: str) -> List[float]:
    return np.frombuffer(base64.b64decode(text), dtype="<f4").tolist()


def _text_of(parent: ET.Element, name: str) -> Optional[str]:
    node = parent.find(_q(NS_PICTOPY, name))
    return node.text if node is not None else None


def _encode_bag(parent: ET.Element, name: str, items: List[str]) -> None:
    if not items:
        return
    prop = ET.SubElement(parent, _q(NS_PICTOPY, name))
    bag = ET.SubElement(prop, _q(NS_RDF, "Bag"))
    for item in items:
        ET.SubElement(bag, _q(NS_RDF, "li")).text = item


def _decode_bag(parent: ET.Element, name: str) -> List[str]:
    node = parent.find(_q(NS_PICTOPY, name))
    if node is None:
        return []
    return [li.text or "" for li in node.iter(_q(NS_RDF, "li"))]


# Sections: one encode/decode pair per field, so each can change on its own.
_Encode = Callable[[PictoPyMetadata, ET.Element], None]
_Decode = Callable[[ET.Element, PictoPyMetadata], None]


def _enc_tags(m: PictoPyMetadata, p: ET.Element) -> None:
    _encode_bag(p, "Tags", m.tags)


def _dec_tags(p: ET.Element, m: PictoPyMetadata) -> None:
    m.tags = _decode_bag(p, "Tags")


def _enc_semantic(m: PictoPyMetadata, p: ET.Element) -> None:
    _encode_bag(p, "SemanticTags", m.semantic_tags)


def _dec_semantic(p: ET.Element, m: PictoPyMetadata) -> None:
    m.semantic_tags = _decode_bag(p, "SemanticTags")


def _enc_albums(m: PictoPyMetadata, p: ET.Element) -> None:
    _encode_bag(p, "Albums", m.albums)


def _dec_albums(p: ET.Element, m: PictoPyMetadata) -> None:
    m.albums = _decode_bag(p, "Albums")


def _enc_favourite(m: PictoPyMetadata, p: ET.Element) -> None:
    if m.favourite is not None:
        ET.SubElement(p, _q(NS_PICTOPY, "Favourite")).text = str(m.favourite).lower()


def _dec_favourite(p: ET.Element, m: PictoPyMetadata) -> None:
    text = _text_of(p, "Favourite")
    if text is not None:
        m.favourite = text.strip().lower() == "true"


def _enc_faces(m: PictoPyMetadata, p: ET.Element) -> None:
    if not m.faces:
        return
    prop = ET.SubElement(p, _q(NS_PICTOPY, "Faces"))
    seq = ET.SubElement(prop, _q(NS_RDF, "Seq"))
    for face in m.faces:
        li = ET.SubElement(seq, _q(NS_RDF, "li"))
        item = ET.SubElement(li, _q(NS_RDF, "Description"))
        ET.SubElement(item, _q(NS_PICTOPY, "Embedding")).text = _vec_to_text(
            face.embedding
        )
        if face.bbox is not None:
            ET.SubElement(item, _q(NS_PICTOPY, "BBox")).text = json.dumps(face.bbox)
        if face.confidence is not None:
            conf = ET.SubElement(item, _q(NS_PICTOPY, "Confidence"))
            conf.text = repr(float(face.confidence))
        if face.cluster_name:
            name = ET.SubElement(item, _q(NS_PICTOPY, "ClusterName"))
            name.text = face.cluster_name


def _dec_faces(p: ET.Element, m: PictoPyMetadata) -> None:
    node = p.find(_q(NS_PICTOPY, "Faces"))
    if node is None:
        return
    for item in node.iter(_q(NS_RDF, "Description")):
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
    version = ET.SubElement(desc, _q(NS_PICTOPY, "ModelVersion"))
    version.text = m.image_embedding.model_version
    vector = ET.SubElement(desc, _q(NS_PICTOPY, "Vector"))
    vector.text = _vec_to_text(m.image_embedding.vector)


def _dec_embedding(p: ET.Element, m: PictoPyMetadata) -> None:
    node = p.find(_q(NS_PICTOPY, "ImageEmbedding"))
    if node is None:
        return
    desc = node.find(_q(NS_RDF, "Description"))
    if desc is None:
        return
    version, vector = _text_of(desc, "ModelVersion"), _text_of(desc, "Vector")
    if version and vector:
        m.image_embedding = EmbeddingRecord(version, _text_to_vec(vector))


# Add a section here to export a new kind of data; nothing else needs to change.
SECTIONS: List[Tuple[str, _Encode, _Decode]] = [
    ("tags", _enc_tags, _dec_tags),
    ("semantic_tags", _enc_semantic, _dec_semantic),
    ("faces", _enc_faces, _dec_faces),
    ("image_embedding", _enc_embedding, _dec_embedding),
    ("favourite", _enc_favourite, _dec_favourite),
    ("albums", _enc_albums, _dec_albums),
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


def _is_ours(desc: ET.Element) -> bool:
    return any(child.tag.startswith(f"{{{NS_PICTOPY}}}") for child in desc)


def _xmpmeta_and_rdf(existing: Optional[bytes]) -> Tuple[ET.Element, ET.Element]:
    if existing:
        try:
            root = _parse(existing)
            rdf = root.find(_q(NS_RDF, "RDF"))
            if root.tag == _q(NS_X, "xmpmeta") and rdf is not None:
                return root, rdf
        except (ET.ParseError, ValueError):
            logger.warning("Existing XMP unreadable; writing a fresh packet")
    root = ET.Element(_q(NS_X, "xmpmeta"))
    return root, ET.SubElement(root, _q(NS_RDF, "RDF"))


class PictoPyXmpCodec:
    """Stores PictoPy data as `pictopy:` properties in a standard XMP packet."""

    def encode(
        self, metadata: PictoPyMetadata, existing: Optional[bytes] = None
    ) -> bytes:
        root, rdf = _xmpmeta_and_rdf(existing)
        # Replace only our own description; other tools' properties survive.
        for desc in rdf.findall(_q(NS_RDF, "Description")):
            if _is_ours(desc):
                rdf.remove(desc)

        ours = ET.SubElement(rdf, _q(NS_RDF, "Description"))
        ours.set(_q(NS_RDF, "about"), "")
        version = ET.SubElement(ours, _q(NS_PICTOPY, "SchemaVersion"))
        version.text = str(metadata.schema_version)
        for _name, enc, _dec in SECTIONS:
            enc(metadata, ours)

        body = ET.tostring(root, encoding="unicode")
        return f"{_XPACKET_BEGIN}\n{body}\n{_XPACKET_END}".encode("utf-8")

    def decode(self, packet: bytes) -> Optional[PictoPyMetadata]:
        try:
            root = _parse(packet)
        except (ET.ParseError, ValueError) as e:
            logger.warning(f"Unreadable XMP packet: {e}")
            return None

        ours = next(
            (d for d in root.iter(_q(NS_RDF, "Description")) if _is_ours(d)), None
        )
        if ours is None:
            return None

        try:
            version = int(_text_of(ours, "SchemaVersion") or 0)
        except ValueError:
            return None
        # Newer data may encode sections differently; do not guess.
        if version < 1 or version > SCHEMA_VERSION:
            return None

        metadata = PictoPyMetadata(schema_version=version)
        for name, _enc, dec in SECTIONS:
            # One bad section must not discard the others.
            try:
                dec(ours, metadata)
            except Exception as e:
                logger.warning(f"Skipping malformed XMP section '{name}': {e}")
        return metadata
