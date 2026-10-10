"""
What leaves the machine when a PNG is shared, and what export does to files it
cannot fully read. Built on a real photo carrying the metadata other tools
write: EXIF, an ICC profile, PNG text, and a Lightroom-style XMP packet.
"""

import io
import os
import shutil
import struct
import xml.etree.ElementTree as ET
import zlib
from typing import Dict, List, Optional, Set, Tuple

import pytest
from PIL import Image, ImageCms
from PIL.PngImagePlugin import PngInfo

from app.utils.xmp import (
    FaceRecord,
    PictoPyMetadata,
    WriteOutcome,
    open_without_pictopy,
    read_image_metadata,
    write_image_metadata,
)
from app.utils.xmp.codec import NS_PICTOPY
from app.utils.xmp.containers import png as png_module

SOURCE_PHOTO = os.path.join(os.path.dirname(__file__), "inputs", "test_2_faces.png")
NS = NS_PICTOPY.encode()
SECRET = "SECRET-FACE-NAME"
KEEP = "KEEP-ME"

XPACKET_BEGIN = '<?xpacket begin="﻿" id="W5M0MpCehiHzreSzNTczkc9d"?>'.encode()
XPACKET_END = b'<?xpacket end="w"?>'
RDF = b'xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"'

# Shaped like what Lightroom Classic writes: one description, attribute-form
# simple properties, and Seq/Bag/Alt arrays.
LIGHTROOM_XMP = (
    XPACKET_BEGIN
    + b'\n<x:xmpmeta xmlns:x="adobe:ns:meta/" x:xmptk="Adobe XMP Core 7.0-c000">\n'
    + b" <rdf:RDF "
    + RDF
    + b">\n"
    + b'  <rdf:Description rdf:about=""\n'
    + b'    xmlns:xmp="http://ns.adobe.com/xap/1.0/"\n'
    + b'    xmlns:dc="http://purl.org/dc/elements/1.1/"\n'
    + b'    xmlns:photoshop="http://ns.adobe.com/photoshop/1.0/"\n'
    + b'    xmlns:lr="http://ns.adobe.com/lightroom/1.0/"\n'
    + b'    xmlns:xmpMM="http://ns.adobe.com/xap/1.0/mm/"\n'
    + b'    xmp:CreatorTool="Adobe Photoshop Lightroom Classic 13.0"\n'
    + b'    xmp:Rating="4"\n'
    + b'    photoshop:DateCreated="2024-07-14T18:32:05"\n'
    + b'    xmpMM:DocumentID="xmp.did:7f1c2d3e-0000-4a5b-9c8d-112233445566">\n'
    + b"   <dc:creator><rdf:Seq><rdf:li>Jane Photographer</rdf:li></rdf:Seq></dc:creator>\n"
    + b'   <dc:title><rdf:Alt><rdf:li xml:lang="x-default">Goa sunset</rdf:li>'
    + '<rdf:li xml:lang="hi-IN">गोवा सूर्यास्त</rdf:li>'.encode()
    + b"</rdf:Alt></dc:title>\n"
    + b"   <dc:subject><rdf:Bag><rdf:li>beach</rdf:li><rdf:li>family</rdf:li>"
    + b"</rdf:Bag></dc:subject>\n"
    + b"   <lr:hierarchicalSubject><rdf:Bag><rdf:li>Places|India|Goa</rdf:li>"
    + b"</rdf:Bag></lr:hierarchicalSubject>\n"
    + b"  </rdf:Description>\n"
    + b" </rdf:RDF>\n"
    + b"</x:xmpmeta>\n"
    + XPACKET_END
)


# --- building realistic files -----------------------------------------------


def _chunk(chunk_type: bytes, body: bytes) -> bytes:
    crc = struct.pack(">I", zlib.crc32(chunk_type + body) & 0xFFFFFFFF)
    return struct.pack(">I", len(body)) + chunk_type + body + crc


def _xmp_chunk(packet: bytes, compressed: bool = False) -> bytes:
    text = zlib.compress(packet) if compressed else packet
    flag = b"\x01" if compressed else b"\x00"
    return _chunk(b"iTXt", b"XML:com.adobe.xmp\x00" + flag + b"\x00\x00\x00" + text)


def _chunks(data: bytes) -> List[Tuple[bytes, bytes]]:
    out, pos = [], 8
    while pos + 8 <= len(data):
        (length,) = struct.unpack(">I", data[pos : pos + 4])
        out.append((data[pos + 4 : pos + 8], data[pos + 8 : pos + 8 + length]))
        pos += 12 + length
    return out


def _xmp_chunks(data: bytes) -> List[bytes]:
    return [
        b for t, b in _chunks(data) if t == b"iTXt" and b.startswith(b"XML:com.adobe")
    ]


def _insert_before_idat(path: str, *chunks: bytes) -> None:
    with open(path, "rb") as f:
        data = f.read()
    at = data.index(b"IDAT") - 4
    with open(path, "wb") as f:
        f.write(data[:at] + b"".join(chunks) + data[at:])


def _photo(tmp_path, name: str = "photo.png", third_party: bool = True) -> str:
    """A copy of a real photo; with third_party, carrying other tools' metadata."""
    path = str(tmp_path / name)
    if not third_party:
        shutil.copy(SOURCE_PHOTO, path)
        return path
    image = Image.open(SOURCE_PHOTO)
    exif = Image.Exif()
    exif[0x013B] = "Jane Photographer"  # Artist
    exif[0x010F] = "Canon"  # Make
    exif[0x0110] = "EOS R6"  # Model
    exif.get_ifd(0x8769)[0x9003] = "2024:07:14 18:32:05"  # DateTimeOriginal
    info = PngInfo()
    info.add_text("Author", "Jane Photographer")
    info.add_text("Comment", "Family trip")
    info.add_itxt("Description", "Café at the beach — 海滩")
    icc = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
    image.save(path, exif=exif, pnginfo=info, icc_profile=icc)
    _insert_before_idat(path, _xmp_chunk(LIGHTROOM_XMP))
    return path


def _export(path: str) -> None:
    """PictoPy's own export, with face data worth protecting."""
    outcome = write_image_metadata(
        path,
        PictoPyMetadata(
            tags=["person"],
            faces=[
                FaceRecord(
                    embedding=[0.25] * 128,
                    bbox={"x": 1, "y": 2, "width": 30, "height": 40},
                    confidence=0.97,
                    cluster_name=SECRET,
                )
            ],
            albums=["Private family album"],
        ),
    )
    assert outcome is WriteOutcome.WRITTEN


# --- inspecting what was served ---------------------------------------------


def _facts(packet: bytes) -> Set[Tuple[str, str]]:
    """Every non-PictoPy value in an XMP packet, as (element path, value)."""
    root = ET.fromstring(packet)
    facts: Set[Tuple[str, str]] = set()

    def walk(el: ET.Element, trail: str) -> None:
        here = f"{trail}/{el.tag}"
        if NS_PICTOPY in el.tag:
            return
        for name, value in el.attrib.items():
            if NS_PICTOPY not in name:
                facts.add((f"{here}@{name}", value))
        if el.text and el.text.strip():
            facts.add((here, el.text.strip()))
        for child in el:
            walk(child, here)

    walk(root, "")
    return facts


def _text_of_xmp(chunk_body: bytes) -> bytes:
    rest = chunk_body[len(b"XML:com.adobe.xmp") + 1 :]
    text = rest[2:].split(b"\x00", 2)[2]
    return zlib.decompress(text) if rest[0] else text


def _other_metadata(data: bytes) -> Dict[str, object]:
    image = Image.open(io.BytesIO(data))
    image.load()
    return {
        "exif": dict(image.getexif()),
        "exif_ifd": dict(image.getexif().get_ifd(0x8769)),
        "icc": image.info.get("icc_profile"),
        "text": {k: v for k, v in image.text.items() if k != "XML:com.adobe.xmp"},
    }


def _serve(path: str, reference: Optional[str] = None) -> bytes:
    """Serve the file and prove the original was not touched in the process.

    `reference` supplies the expected pixels when the original itself cannot
    be opened (Pillow rejects a PNG whose compressed XMP is corrupt).
    """
    with open(path, "rb") as f:
        before = f.read()
    mtime = os.stat(path).st_mtime_ns

    stream = open_without_pictopy(path)
    assert stream is not None
    served = b"".join(stream.chunks)
    assert len(served) == stream.length

    with open(path, "rb") as f:
        assert f.read() == before
    assert os.stat(path).st_mtime_ns == mtime
    # Pixel-identical, and a structurally valid PNG.
    expected = Image.open(reference or path).tobytes()
    assert Image.open(io.BytesIO(served)).tobytes() == expected
    Image.open(io.BytesIO(served)).verify()
    return served


def _assert_no_pictopy(served: bytes) -> None:
    assert NS not in served
    assert SECRET.encode() not in served
    assert b"Private family album" not in served


# --- the three kinds of file ------------------------------------------------


class TestFileKinds:
    def test_no_pictopy_metadata_is_served_byte_identical(self, tmp_path):
        path = _photo(tmp_path)
        with open(path, "rb") as f:
            assert _serve(path) == f.read()

    def test_only_pictopy_metadata_is_removed_entirely(self, tmp_path):
        path = _photo(tmp_path, third_party=False)
        _export(path)
        with open(path, "rb") as f:
            assert SECRET.encode() in f.read()

        served = _serve(path)
        _assert_no_pictopy(served)
        assert _xmp_chunks(served) == []

    def test_pictopy_and_third_party_metadata(self, tmp_path):
        path = _photo(tmp_path)
        original = _other_metadata(open(path, "rb").read())
        _export(path)
        with open(path, "rb") as f:
            on_disk = f.read()
        # Export merged into Lightroom's packet rather than adding a second one.
        assert len(_xmp_chunks(on_disk)) == 1

        served = _serve(path)
        _assert_no_pictopy(served)
        [chunk] = _xmp_chunks(served)
        assert _facts(_text_of_xmp(chunk)) == _facts(LIGHTROOM_XMP)
        assert _other_metadata(served) == original

    def test_separate_third_party_packet_is_passed_through_unchanged(self, tmp_path):
        # Two XMP chunks is non-standard, but a tool could leave one behind.
        path = _photo(tmp_path, third_party=False)
        _export(path)
        _insert_before_idat(path, _xmp_chunk(LIGHTROOM_XMP))

        served = _serve(path)
        _assert_no_pictopy(served)
        assert [_text_of_xmp(c) for c in _xmp_chunks(served)] == [LIGHTROOM_XMP]


# --- PictoPy data wherever another tool may have moved it -------------------

DC = b'xmlns:dc="http://purl.org/dc/elements/1.1/"'
PP = b'xmlns:pictopy="https://pictopy.app/ns/1.0/"'
S, K = SECRET.encode(), KEEP.encode()


def _packet(body: bytes, ns: bytes = DC + b" " + PP) -> bytes:
    return (
        b'<x:xmpmeta xmlns:x="adobe:ns:meta/"><rdf:RDF '
        + RDF
        + b'><rdf:Description rdf:about="" '
        + ns
        + b">"
        + body
        + b"</rdf:Description></rdf:RDF></x:xmpmeta>"
    )


NESTED = {
    "attribute on the description": _packet(
        b"<dc:creator>" + K + b"</dc:creator>",
        ns=DC + b" " + PP + b' pictopy:ClusterName="' + S + b'"',
    ),
    "element beside foreign ones": _packet(
        b"<dc:creator>" + K + b"</dc:creator><pictopy:ClusterName>" + S
        + b"</pictopy:ClusterName>"
    ),  # fmt: skip
    "inside a foreign bag item": _packet(
        b"<dc:subject><rdf:Bag><rdf:li>" + K + b"</rdf:li><rdf:li>"
        b"<pictopy:ClusterName>" + S + b"</pictopy:ClusterName>"
        b"</rdf:li></rdf:Bag></dc:subject>"
    ),
    "inside a foreign struct": _packet(
        b"<dc:relation><rdf:Description><dc:title>" + K + b"</dc:title>"
        b"<pictopy:Faces><rdf:Seq><rdf:li>" + S + b"</rdf:li></rdf:Seq>"
        b"</pictopy:Faces></rdf:Description></dc:relation>"
    ),
    "attribute on a nested element": _packet(
        b"<dc:subject><rdf:Bag><rdf:li pictopy:Name=\"" + S + b"\">" + K
        + b"</rdf:li></rdf:Bag></dc:subject>"
    ),  # fmt: skip
    "five levels deep": _packet(
        b"<dc:a><rdf:Description><dc:b><rdf:Description><dc:c><rdf:Bag><rdf:li>"
        b"<pictopy:ClusterName>" + S + b"</pictopy:ClusterName></rdf:li>"
        b"<rdf:li>" + K + b"</rdf:li></rdf:Bag></dc:c></rdf:Description>"
        b"</dc:b></rdf:Description></dc:a>"
    ),
    "another prefix bound to our namespace": _packet(
        b"<dc:creator>" + K + b"</dc:creator><pp:ClusterName>" + S
        + b"</pp:ClusterName>",
        ns=DC + b' xmlns:pp="https://pictopy.app/ns/1.0/"',
    ),  # fmt: skip
    "default namespace on a nested element": _packet(
        b"<dc:creator>" + K + b"</dc:creator>"
        b'<ClusterName xmlns="https://pictopy.app/ns/1.0/">' + S + b"</ClusterName>",
        ns=DC,
    ),
    "namespace spelled with character references": _packet(
        b"<dc:creator>" + K + b"</dc:creator><p:ClusterName>" + S
        + b"</p:ClusterName>",
        ns=DC + b' xmlns:p="&#104;ttps://pictopy.app/ns/1.0/"',
    ),  # fmt: skip
    "bare rdf:RDF root": b"<rdf:RDF "
    + RDF
    + b'><rdf:Description rdf:about="" '
    + DC
    + b" "
    + PP
    + b"><dc:creator>"
    + K
    + b"</dc:creator><pictopy:ClusterName>"
    + S
    + b"</pictopy:ClusterName></rdf:Description></rdf:RDF>",
}


class TestNestedPictoPyData:
    @pytest.mark.parametrize("case", sorted(NESTED))
    def test_removed_at_every_level_and_foreign_kept(self, tmp_path, case):
        path = _photo(tmp_path, third_party=False)
        _insert_before_idat(path, _xmp_chunk(NESTED[case]))

        served = _serve(path)
        assert S not in served
        [chunk] = _xmp_chunks(served)
        packet = _text_of_xmp(chunk)
        assert _facts(packet) == _facts(NESTED[case])
        assert K in packet

    def test_pictopy_root_element_cannot_be_stripped_so_packet_is_dropped(
        self, tmp_path
    ):
        path = _photo(tmp_path, third_party=False)
        packet = b"<pictopy:Faces " + PP + b"><dc:x " + DC + b">" + S + b"</dc:x>"
        _insert_before_idat(path, _xmp_chunk(packet + b"</pictopy:Faces>"))
        served = _serve(path)
        assert S not in served
        assert _xmp_chunks(served) == []


# --- malformed and corrupt packets: exactly what is kept and what is dropped -


BROKEN_FOREIGN = (
    b'<x:xmpmeta xmlns:x="adobe:ns:meta/"><rdf:RDF '
    + RDF
    + b"><rdf:Description "
    + DC
    + b"><dc:creator>"
    + K
    + b"</dc:creator></rdf:RDF>"  # description never closed
)


class TestMalformedPackets:
    def _with(self, tmp_path, *chunks: bytes) -> str:
        path = _photo(tmp_path)
        shutil.copy(path, tmp_path / "reference.png")
        # Replace the healthy Lightroom packet with the case under test.
        with open(path, "rb") as f:
            data = f.read()
        healthy = _xmp_chunk(LIGHTROOM_XMP)
        with open(path, "wb") as f:
            f.write(data.replace(healthy, b"".join(chunks)))
        return path

    def _rest_is_intact(self, served: bytes, reference: str) -> None:
        with open(reference, "rb") as f:
            assert _other_metadata(served) == _other_metadata(f.read())

    def test_malformed_foreign_packet_is_kept_byte_identical(self, tmp_path):
        path = self._with(tmp_path, _xmp_chunk(BROKEN_FOREIGN))
        with open(path, "rb") as f:
            assert _serve(path) == f.read()

    def test_foreign_packet_with_doctype_is_kept_byte_identical(self, tmp_path):
        packet = b"<!DOCTYPE x:xmpmeta>" + LIGHTROOM_XMP.split(b"?>", 1)[1]
        path = self._with(tmp_path, _xmp_chunk(packet))
        with open(path, "rb") as f:
            assert _serve(path) == f.read()

    def test_malformed_packet_holding_pictopy_data_is_dropped(self, tmp_path):
        # Cannot be separated, so the whole packet stays home; everything
        # outside it (EXIF, ICC, text) is still sent.
        broken = BROKEN_FOREIGN.replace(
            b"<dc:creator>", PP.join([b"<pictopy:ClusterName ", b">"]) + S
        )
        path = self._with(tmp_path, _xmp_chunk(broken))
        served = _serve(path)
        assert S not in served and NS not in served
        assert _xmp_chunks(served) == []
        self._rest_is_intact(served, str(tmp_path / "reference.png"))

    def test_corrupt_compressed_packet_is_dropped(self, tmp_path):
        chunk = bytearray(_xmp_chunk(LIGHTROOM_XMP, compressed=True))
        chunk[-8:-4] = b"XXXX"  # zlib checksum
        path = self._with(tmp_path, bytes(chunk))
        with pytest.raises(Exception):
            Image.open(path).load()  # the original is unreadable to Pillow
        reference = str(tmp_path / "reference.png")
        served = _serve(path, reference)
        assert _xmp_chunks(served) == []
        self._rest_is_intact(served, reference)

    def test_compressed_pictopy_packet_is_stripped_and_foreign_kept(self, tmp_path):
        path = _photo(tmp_path)
        _export(path)
        with open(path, "rb") as f:
            [body] = _xmp_chunks(f.read())
        merged = _text_of_xmp(body)
        path2 = self._with(tmp_path, _xmp_chunk(merged, compressed=True))
        served = _serve(path2)
        _assert_no_pictopy(served)
        [chunk] = _xmp_chunks(served)
        assert _facts(_text_of_xmp(chunk)) == _facts(LIGHTROOM_XMP)

    def test_malformed_chunk_header_without_our_namespace_is_kept(self, tmp_path):
        bad = _chunk(b"iTXt", b"XML:com.adobe.xmp\x00\x00\x00no-separators " + K)
        path = self._with(tmp_path, bad)
        with open(path, "rb") as f:
            assert _serve(path) == f.read()

    def test_malformed_chunk_header_with_our_namespace_is_dropped(self, tmp_path):
        bad = _chunk(b"iTXt", b"XML:com.adobe.xmp\x00\x00\x00" + NS + S)
        path = self._with(tmp_path, bad)
        served = _serve(path)
        assert S not in served
        self._rest_is_intact(served, str(tmp_path / "reference.png"))

    def test_oversized_packet_is_scanned_not_dropped_blindly(
        self, tmp_path, monkeypatch
    ):
        clean = self._with(tmp_path, _xmp_chunk(LIGHTROOM_XMP))
        dirty = _photo(tmp_path, "dirty.png")
        _export(dirty)
        # Both packets are now "too large to rewrite"; small blocks also make
        # the marker straddle block boundaries.
        monkeypatch.setattr(png_module, "MAX_PACKET_BYTES", 64)
        monkeypatch.setattr(png_module, "STREAM_BLOCK_BYTES", 16)
        with open(clean, "rb") as f:
            assert _serve(clean) == f.read()
        served = _serve(dirty)
        _assert_no_pictopy(served)
        assert _xmp_chunks(served) == []

    @pytest.mark.parametrize("block", [1, 7, 26, 27, 28, 4096])
    def test_marker_is_found_across_any_block_boundary(self, block):
        marker = NS
        for at in range(0, 40):
            data = b"x" * at + marker + b"y" * 13
            f = io.BytesIO(data)
            with pytest.MonkeyPatch.context() as mp:
                mp.setattr(png_module, "STREAM_BLOCK_BYTES", block)
                assert png_module._contains(f, len(data), [marker])
            clean = io.BytesIO(data.replace(marker, b"z" * len(marker)))
            with pytest.MonkeyPatch.context() as mp:
                mp.setattr(png_module, "STREAM_BLOCK_BYTES", block)
                assert not png_module._contains(clean, len(data), [marker])


# --- the namespace spelled some other way, in packets that cannot be parsed --
#
# A parsed packet is judged by its tree, which resolves every spelling. These
# cover the packets we cannot parse: besides literally, XML can spell our
# namespace only with numeric character references, declared entities, or in
# UTF-16/32. PictoPy always writes it literally in UTF-8, so these exist only
# if another tool both re-encodes our data and breaks the XML.

UNCLOSED = b"<dc:creator>" + K + b"</dc:creator>"  # description never closed


def _broken(ns_decl: bytes, body: bytes = b"") -> bytes:
    return (
        b'<x:xmpmeta xmlns:x="adobe:ns:meta/"><rdf:RDF '
        + RDF
        + b'><rdf:Description rdf:about="" '
        + DC
        + b" "
        + ns_decl
        + b">"
        + UNCLOSED
        + body
        + b"</rdf:RDF></x:xmpmeta>"
    )


SPELLINGS = {
    "decimal character reference": b'xmlns:p="&#104;ttps://pictopy.app/ns/1.0/"',
    "hex character reference": b'xmlns:p="&#x68;ttps://pictopy.app/ns/1.0/"',
    "every character referenced": b'xmlns:p="'
    + b"".join(b"&#%d;" % ord(c) for c in NS_PICTOPY)
    + b'"',
}


class TestNamespaceSpelledOtherwise:
    @pytest.mark.parametrize("case", sorted(SPELLINGS))
    def test_unparseable_packet_with_escaped_namespace_is_dropped(self, tmp_path, case):
        packet = _broken(SPELLINGS[case], b"<p:ClusterName>" + S + b"</p:ClusterName>")
        assert NS not in packet  # the literal check alone would miss it
        path = _photo(tmp_path, third_party=False)
        _insert_before_idat(path, _xmp_chunk(packet))
        served = _serve(path)
        assert S not in served
        assert _xmp_chunks(served) == []

    def test_entity_declaration_is_treated_as_possibly_ours(self, tmp_path):
        packet = (
            b'<!DOCTYPE x [<!ENTITY h "https">]>'
            + _broken(b'xmlns:p="&h;://pictopy.app/ns/1.0/"')
            + b"<p:ClusterName>"
            + S
            + b"</p:ClusterName>"
        )
        path = _photo(tmp_path, third_party=False)
        _insert_before_idat(path, _xmp_chunk(packet))
        assert S not in _serve(path)

    def test_utf16_packet_is_treated_as_possibly_ours(self, tmp_path):
        packet = _broken(PP, b"<pictopy:ClusterName>" + S + b"</pictopy:ClusterName>")
        utf16 = packet.decode().encode("utf-16-le")
        assert NS not in utf16 and S not in utf16
        path = _photo(tmp_path, third_party=False)
        _insert_before_idat(path, _xmp_chunk(utf16))
        served = _serve(path)
        assert SECRET.encode("utf-16-le") not in served

    def test_ordinary_escapes_in_foreign_packets_are_not_a_reason_to_drop(
        self, tmp_path
    ):
        # Lightroom and exiftool write captions with &#xA; for newlines.
        packet = _broken(b"", b"<dc:description>line&#xA;break&#233;</dc:description>")
        path = _photo(tmp_path, third_party=False)
        _insert_before_idat(path, _xmp_chunk(packet))
        with open(path, "rb") as f:
            assert _serve(path) == f.read()

    def test_unreadable_chunk_with_escaped_namespace_is_dropped(self, tmp_path):
        # Broken block header: nothing can parse it, so any spelling counts.
        body = b"XML:com.adobe.xmp\x00\x00\x00p:x &#104;ttps://pictopy.app/ns/1.0/ " + S
        path = _photo(tmp_path, third_party=False)
        _insert_before_idat(path, _chunk(b"iTXt", body))
        assert S not in _serve(path)

    @pytest.mark.parametrize("encoding", ["utf-8", "utf-16-le", "utf-32-be"])
    def test_oversized_packet_with_escaped_namespace_is_dropped(
        self, tmp_path, monkeypatch, encoding
    ):
        packet = _broken(SPELLINGS["hex character reference"])
        packet = packet.decode().encode(encoding) + SECRET.encode(encoding)
        path = _photo(tmp_path, third_party=False)
        _insert_before_idat(path, _xmp_chunk(packet))
        monkeypatch.setattr(png_module, "MAX_PACKET_BYTES", 64)
        monkeypatch.setattr(png_module, "STREAM_BLOCK_BYTES", 16)
        assert SECRET.encode(encoding) not in _serve(path)


# --- export must never destroy metadata it cannot read ----------------------


class TestExportNeverDestroysUnreadableXmp:
    def _unchanged_after_export(self, path: str) -> None:
        with open(path, "rb") as f:
            before = f.read()
        assert write_image_metadata(path, PictoPyMetadata(tags=["x"])) is (
            WriteOutcome.UNREADABLE_EXISTING
        )
        with open(path, "rb") as f:
            assert f.read() == before

    def test_malformed_foreign_packet(self, tmp_path):
        path = _photo(tmp_path, third_party=False)
        _insert_before_idat(path, _xmp_chunk(BROKEN_FOREIGN))
        self._unchanged_after_export(path)

    def test_foreign_packet_with_doctype(self, tmp_path):
        path = _photo(tmp_path, third_party=False)
        _insert_before_idat(path, _xmp_chunk(b"<!DOCTYPE x>" + _packet(b"")))
        self._unchanged_after_export(path)

    def test_two_xmp_packets(self, tmp_path):
        path = _photo(tmp_path)
        _insert_before_idat(path, _xmp_chunk(LIGHTROOM_XMP))
        self._unchanged_after_export(path)

    def test_corrupt_compressed_packet(self, tmp_path):
        chunk = bytearray(_xmp_chunk(LIGHTROOM_XMP, compressed=True))
        chunk[-8:-4] = b"XXXX"
        path = _photo(tmp_path, third_party=False)
        _insert_before_idat(path, bytes(chunk))
        self._unchanged_after_export(path)

    def test_malformed_chunk_header(self, tmp_path):
        path = _photo(tmp_path, third_party=False)
        _insert_before_idat(path, _chunk(b"iTXt", b"XML:com.adobe.xmp\x00\x00\x00x"))
        self._unchanged_after_export(path)

    def test_oversized_packet(self, tmp_path, monkeypatch):
        monkeypatch.setattr(png_module, "MAX_PACKET_BYTES", 64)
        path = _photo(tmp_path)
        self._unchanged_after_export(path)

    def test_lightroom_metadata_survives_export_intact(self, tmp_path):
        path = _photo(tmp_path)
        with open(path, "rb") as f:
            before = _other_metadata(f.read())
        _export(path)
        with open(path, "rb") as f:
            after = f.read()
        [chunk] = _xmp_chunks(after)
        assert _facts(_text_of_xmp(chunk)) >= _facts(LIGHTROOM_XMP)
        assert _other_metadata(after) == before
        decoded = read_image_metadata(path)
        assert decoded is not None and decoded.faces[0].cluster_name == SECRET

    def test_bare_rdf_root_is_merged_not_replaced(self, tmp_path):
        path = _photo(tmp_path, third_party=False)
        packet = NESTED["bare rdf:RDF root"]
        _insert_before_idat(path, _xmp_chunk(packet))
        assert write_image_metadata(path, PictoPyMetadata(tags=["x"])) is (
            WriteOutcome.WRITTEN
        )
        with open(path, "rb") as f:
            [chunk] = _xmp_chunks(f.read())
        written = _text_of_xmp(chunk)
        assert K in written and S not in written

    def test_stale_nested_pictopy_data_is_replaced_not_kept(self, tmp_path):
        path = _photo(tmp_path, third_party=False)
        _insert_before_idat(path, _xmp_chunk(NESTED["inside a foreign bag item"]))
        write_image_metadata(path, PictoPyMetadata(tags=["x"]))
        with open(path, "rb") as f:
            [chunk] = _xmp_chunks(f.read())
        written = _text_of_xmp(chunk)
        assert S not in written and K in written
        decoded: Optional[PictoPyMetadata] = read_image_metadata(path)
        assert decoded is not None and decoded.tags == ["x"]
