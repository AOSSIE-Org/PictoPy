"""
Building and reading the XMP packet PictoPy embeds in a photo.

Pure string and tree work: nothing here touches a file. The packet is the
portable half of a photo's metadata, so only properties with a real home in a
published schema belong in it -- album membership and embeddings stay in SQLite.

Merging matters more than writing. A photo may already carry XMP from Lightroom
or digiKam, and replacing that packet wholesale would silently discard someone
else's captions, ratings and edit history.
"""

import re
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional, Tuple, TypedDict

from app.logging.setup_logging import get_logger

logger = get_logger(__name__)

NS_X = "adobe:ns:meta/"
NS_RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
NS_DC = "http://purl.org/dc/elements/1.1/"
NS_XMP = "http://ns.adobe.com/xap/1.0/"
NS_LR = "http://ns.adobe.com/lightroom/1.0/"
NS_MWG_RS = "http://www.metadataworkinggroup.com/schemas/regions/"
NS_ST_AREA = "http://ns.adobe.com/xmp/sType/Area#"
NS_ST_DIM = "http://ns.adobe.com/xap/1.0/sType/Dimensions#"
NS_PICTOPY = "https://github.com/AOSSIE-Org/PictoPy/ns/1.0/"

_PREFIXES = {
    "x": NS_X,
    "rdf": NS_RDF,
    "dc": NS_DC,
    "xmp": NS_XMP,
    "lr": NS_LR,
    "mwg-rs": NS_MWG_RS,
    "stArea": NS_ST_AREA,
    "stDim": NS_ST_DIM,
    "pictopy": NS_PICTOPY,
}

# Properties PictoPy considers its own. Anything else in the packet belongs to
# another application and is copied through untouched.
_OWNED = (
    f"{{{NS_DC}}}subject",
    f"{{{NS_LR}}}hierarchicalSubject",
    f"{{{NS_XMP}}}Rating",
    f"{{{NS_XMP}}}MetadataDate",
    f"{{{NS_MWG_RS}}}Regions",
    f"{{{NS_PICTOPY}}}WrittenAt",
)

_XMPMETA = re.compile(rb"<x:xmpmeta[^>]*>.*</x:xmpmeta>", re.S)
# The xmpmeta wrapper is optional; some writers emit a bare rdf:RDF root.
_BARE_RDF = re.compile(rb"<rdf:RDF[^>]*>.*</rdf:RDF>", re.S)

# The XMP specification forbids a DTD inside a packet, and honouring one from an
# arbitrary photo would let a crafted file expand entities until memory runs out.
_DOCTYPE = re.compile(rb"<!DOCTYPE", re.I)

_PACKET_HEADER = b'<?xpacket begin="\xef\xbb\xbf" id="W5M0MpCehiHzreSzNTczkc9d"?>'
_PACKET_TRAILER = b'<?xpacket end="w"?>'


class UnreadablePacketError(Exception):
    """
    A photo carries an XMP packet that cannot be parsed.

    Distinct from carrying none at all: we cannot see what overwriting it would
    destroy, so the caller is expected to leave the file alone.
    """


class FaceRegion(TypedDict):
    """One face, in the normalised centre-based form MWG defines."""

    name: str
    center_x: float
    center_y: float
    width: float
    height: float


class PhotoMetadata(TypedDict, total=False):
    """The portable half of what PictoPy knows about a photo."""

    keywords: List[str]
    hierarchical_keywords: List[str]
    rating: Optional[int]
    regions: List[FaceRegion]
    applied_width: Optional[int]
    applied_height: Optional[int]
    written_at: Optional[str]


def _register_prefixes() -> None:
    for prefix, uri in _PREFIXES.items():
        ET.register_namespace(prefix, uri)


def _qname(uri: str, tag: str) -> str:
    return f"{{{uri}}}{tag}"


def xmp_packet_orient_region(
    bbox: Dict[str, int],
    raw_width: int,
    raw_height: int,
    orientation: int = 1,
) -> Optional[Tuple[float, float, float, float]]:
    """
    Convert a stored face box into MWG's normalised, centre-based coordinates.

    Two mismatches make this less obvious than it looks. Face boxes are recorded
    in the pixel space OpenCV decodes, which ignores the EXIF orientation flag,
    while an MWG region is defined against the image as displayed -- so on a
    rotated photo the untransformed box lands somewhere else entirely. And MWG's
    x and y are the centre of the region, not its corner.

    Returns (centre_x, centre_y, width, height), or None if the box cannot be
    placed inside the image.
    """
    if raw_width <= 0 or raw_height <= 0:
        return None

    width = bbox.get("width", 0)
    height = bbox.get("height", 0)
    if width <= 0 or height <= 0:
        return None

    # Centre first, still in raw pixel space, then normalise.
    raw_cx = (bbox.get("x", 0) + width / 2) / raw_width
    raw_cy = (bbox.get("y", 0) + height / 2) / raw_height
    raw_w = width / raw_width
    raw_h = height / raw_height

    if orientation in (5, 6, 7, 8):
        # The displayed image is rotated a quarter turn, so the box's extents
        # swap along with the frame's.
        raw_w, raw_h = raw_h, raw_w

    transforms = {
        1: (raw_cx, raw_cy),
        2: (1 - raw_cx, raw_cy),
        3: (1 - raw_cx, 1 - raw_cy),
        4: (raw_cx, 1 - raw_cy),
        5: (raw_cy, raw_cx),
        6: (1 - raw_cy, raw_cx),
        7: (1 - raw_cy, 1 - raw_cx),
        8: (raw_cy, 1 - raw_cx),
    }
    center_x, center_y = transforms.get(orientation, (raw_cx, raw_cy))

    if not (0 <= center_x <= 1 and 0 <= center_y <= 1):
        return None

    return (round(center_x, 6), round(center_y, 6), round(raw_w, 6), round(raw_h, 6))


def xmp_packet_applied_dimensions(
    raw_width: int, raw_height: int, orientation: int = 1
) -> Tuple[int, int]:
    """The image's dimensions as displayed, which is what regions are relative to."""
    if orientation in (5, 6, 7, 8):
        return raw_height, raw_width
    return raw_width, raw_height


def _strip_owned(description: ET.Element) -> None:
    """Drop PictoPy's own properties, in both the element and attribute spellings."""
    for child in list(description):
        if child.tag in _OWNED:
            description.remove(child)
    for attribute in list(description.attrib):
        if attribute in _OWNED:
            del description.attrib[attribute]


def _append_bag(parent: ET.Element, uri: str, tag: str, values: List[str]) -> None:
    prop = ET.SubElement(parent, _qname(uri, tag))
    bag = ET.SubElement(prop, _qname(NS_RDF, "Bag"))
    for value in values:
        ET.SubElement(bag, _qname(NS_RDF, "li")).text = value


def _append_regions(
    parent: ET.Element, metadata: PhotoMetadata, regions: List[FaceRegion]
) -> None:
    container = ET.SubElement(parent, _qname(NS_MWG_RS, "Regions"))
    container.set(_qname(NS_RDF, "parseType"), "Resource")

    width = metadata.get("applied_width")
    height = metadata.get("applied_height")
    if width and height:
        dimensions = ET.SubElement(container, _qname(NS_MWG_RS, "AppliedToDimensions"))
        dimensions.set(_qname(NS_ST_DIM, "w"), str(width))
        dimensions.set(_qname(NS_ST_DIM, "h"), str(height))
        dimensions.set(_qname(NS_ST_DIM, "unit"), "pixel")

    region_list = ET.SubElement(container, _qname(NS_MWG_RS, "RegionList"))
    bag = ET.SubElement(region_list, _qname(NS_RDF, "Bag"))
    for region in regions:
        item = ET.SubElement(bag, _qname(NS_RDF, "li"))
        item.set(_qname(NS_RDF, "parseType"), "Resource")
        ET.SubElement(item, _qname(NS_MWG_RS, "Name")).text = region["name"]
        ET.SubElement(item, _qname(NS_MWG_RS, "Type")).text = "Face"
        area = ET.SubElement(item, _qname(NS_MWG_RS, "Area"))
        area.set(_qname(NS_ST_AREA, "x"), f"{region['center_x']:g}")
        area.set(_qname(NS_ST_AREA, "y"), f"{region['center_y']:g}")
        area.set(_qname(NS_ST_AREA, "w"), f"{region['width']:g}")
        area.set(_qname(NS_ST_AREA, "h"), f"{region['height']:g}")
        area.set(_qname(NS_ST_AREA, "unit"), "normalized")


def _parse(packet: bytes) -> Optional[ET.Element]:
    """
    Parse a packet's xmpmeta root, or None if the packet holds none.

    Raises UnreadablePacketError when something is there but cannot be read,
    which is not the same as nothing being there -- see xmp_packet_build.
    """
    if not packet.strip():
        return None

    if _DOCTYPE.search(packet):
        raise UnreadablePacketError("XMP packet carries a DTD")

    found = _XMPMETA.search(packet) or _BARE_RDF.search(packet)
    if not found:
        # Something is in here that we do not recognise as a packet. Treating
        # that as "no metadata" would licence overwriting it.
        raise UnreadablePacketError("XMP packet has no recognisable root")

    try:
        root = ET.fromstring(found.group(0))
    except ET.ParseError as e:
        raise UnreadablePacketError(f"XMP packet is malformed: {e}") from e

    if root.tag == _qname(NS_RDF, "RDF"):
        wrapper = ET.Element(_qname(NS_X, "xmpmeta"))
        wrapper.append(root)
        return wrapper

    return root


def _empty_root() -> ET.Element:
    root = ET.Element(_qname(NS_X, "xmpmeta"))
    ET.SubElement(root, _qname(NS_RDF, "RDF"))
    return root


def xmp_packet_build(
    metadata: PhotoMetadata, existing: Optional[bytes] = None
) -> bytes:
    """
    Render PictoPy's properties into an XMP packet, preserving anything foreign.

    Passing the photo's current packet as `existing` keeps every property this
    module does not own; passing None writes a fresh one.

    Raises UnreadablePacketError if `existing` is present but unparseable. That
    is deliberate: writing anyway would silently destroy whatever the photo was
    carrying, and a file we cannot read is exactly the one not to gamble on.
    """
    _register_prefixes()

    root = _parse(existing) if existing else None
    if root is None:
        root = _empty_root()

    rdf = root.find(_qname(NS_RDF, "RDF"))
    if rdf is None:
        rdf = ET.SubElement(root, _qname(NS_RDF, "RDF"))

    descriptions = rdf.findall(_qname(NS_RDF, "Description"))
    for description in descriptions:
        _strip_owned(description)

    if descriptions:
        target = descriptions[0]
    else:
        target = ET.SubElement(rdf, _qname(NS_RDF, "Description"))
        target.set(_qname(NS_RDF, "about"), "")

    keywords = metadata.get("keywords") or []
    if keywords:
        _append_bag(target, NS_DC, "subject", keywords)

    hierarchical = metadata.get("hierarchical_keywords") or []
    if hierarchical:
        _append_bag(target, NS_LR, "hierarchicalSubject", hierarchical)

    rating = metadata.get("rating")
    if rating is not None:
        ET.SubElement(target, _qname(NS_XMP, "Rating")).text = str(rating)

    regions = metadata.get("regions") or []
    if regions:
        _append_regions(target, metadata, regions)

    written_at = metadata.get("written_at")
    if written_at:
        # Recorded in both places on purpose: xmp:MetadataDate is what other
        # software updates when it edits, so a later value there than ours is
        # how a future import pass can tell someone else touched the file.
        ET.SubElement(target, _qname(NS_XMP, "MetadataDate")).text = written_at
        ET.SubElement(target, _qname(NS_PICTOPY, "WrittenAt")).text = written_at

    body = ET.tostring(root, encoding="utf-8")
    return _PACKET_HEADER + body + _PACKET_TRAILER


def _read_bag(description: ET.Element, uri: str, tag: str) -> List[str]:
    prop = description.find(_qname(uri, tag))
    if prop is None:
        return []
    return [
        item.text or ""
        for item in prop.iterfind(f"{_qname(NS_RDF, 'Bag')}/{_qname(NS_RDF, 'li')}")
    ]


def xmp_packet_read(packet: bytes) -> PhotoMetadata:
    """
    Read back the properties PictoPy owns. Anything missing is simply absent.

    Foreign properties are ignored rather than reported: this exists to verify
    what was written and, later, to import what another application left.
    """
    result: PhotoMetadata = {}
    try:
        root = _parse(packet)
    except UnreadablePacketError as e:
        # Reading is best-effort; only writing needs to stop over this.
        logger.warning(f"Ignoring an unreadable XMP packet: {e}")
        return result
    if root is None:
        return result

    rdf = root.find(_qname(NS_RDF, "RDF"))
    if rdf is None:
        return result

    for description in rdf.findall(_qname(NS_RDF, "Description")):
        keywords = _read_bag(description, NS_DC, "subject")
        if keywords:
            result["keywords"] = keywords

        hierarchical = _read_bag(description, NS_LR, "hierarchicalSubject")
        if hierarchical:
            result["hierarchical_keywords"] = hierarchical

        rating = description.find(_qname(NS_XMP, "Rating"))
        if rating is not None and rating.text:
            try:
                result["rating"] = int(rating.text)
            except ValueError:
                logger.warning(f"Ignoring a non-numeric xmp:Rating: {rating.text!r}")

        written = description.find(_qname(NS_PICTOPY, "WrittenAt"))
        if written is not None and written.text:
            result["written_at"] = written.text

        regions = _read_regions(description)
        if regions:
            result["regions"] = regions

    return result


def _as_float(value: Optional[str]) -> Optional[float]:
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def _read_regions(description: ET.Element) -> List[FaceRegion]:
    container = description.find(_qname(NS_MWG_RS, "Regions"))
    if container is None:
        return []

    regions: List[FaceRegion] = []
    path = (
        f"{_qname(NS_MWG_RS, 'RegionList')}/{_qname(NS_RDF, 'Bag')}/"
        f"{_qname(NS_RDF, 'li')}"
    )
    for item in container.iterfind(path):
        area = item.find(_qname(NS_MWG_RS, "Area"))
        if area is None:
            continue

        values: Dict[str, Any] = {
            key: _as_float(area.get(_qname(NS_ST_AREA, key)))
            for key in ("x", "y", "w", "h")
        }
        if any(value is None for value in values.values()):
            continue

        name = item.find(_qname(NS_MWG_RS, "Name"))
        regions.append(
            FaceRegion(
                name=(name.text or "") if name is not None else "",
                center_x=values["x"],
                center_y=values["y"],
                width=values["w"],
                height=values["h"],
            )
        )

    return regions
