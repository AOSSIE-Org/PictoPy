import struct
import zlib

import numpy as np
import pytest
from PIL import Image

from app.utils.xmp import (
    EmbeddingRecord,
    FaceRecord,
    PictoPyMetadata,
    is_xmp_supported,
    read_image_metadata,
    write_image_metadata,
)
from app.utils.xmp.codec import NS_PICTOPY, PictoPyXmpCodec
from app.utils.xmp.containers.png import PngContainer, PngFormatError


def _sample() -> PictoPyMetadata:
    return PictoPyMetadata(
        tags=["person", "dog"],
        semantic_tags=["beach & sunset"],
        faces=[
            FaceRecord(
                embedding=[0.25, -1.5, 3.0],
                bbox={"x": 10, "y": 20, "width": 30.5, "height": 40},
                confidence=0.98,
                cluster_name="Alice <A>",
            ),
            FaceRecord(embedding=[1.0, 2.0, 3.0]),
        ],
        image_embedding=EmbeddingRecord("siglip2-base", [0.5, 0.125]),
        favourite=True,
        albums=["Trip", "Family"],
    )


@pytest.fixture
def png(tmp_path):
    path = tmp_path / "a.png"
    rng = np.random.default_rng(0)
    Image.fromarray(rng.integers(0, 256, (64, 64, 3), dtype=np.uint8)).save(path)
    return str(path)


def _idat_bytes(path: str) -> bytes:
    data = open(path, "rb").read()
    out, pos = b"", 8
    while pos < len(data):
        (length,) = struct.unpack(">I", data[pos : pos + 4])
        if data[pos + 4 : pos + 8] == b"IDAT":
            out += data[pos + 8 : pos + 8 + length]
        pos += 12 + length
    return out


class TestCodec:
    def test_round_trip(self):
        codec = PictoPyXmpCodec()
        decoded = codec.decode(codec.encode(_sample()))
        assert decoded == _sample()

    def test_empty_metadata_round_trips(self):
        codec = PictoPyXmpCodec()
        assert codec.decode(codec.encode(PictoPyMetadata())) == PictoPyMetadata()

    def test_newer_schema_version_is_ignored(self):
        codec = PictoPyXmpCodec()
        packet = codec.encode(PictoPyMetadata(schema_version=999))
        assert codec.decode(packet) is None

    def test_malformed_section_does_not_drop_others(self):
        codec = PictoPyXmpCodec()
        packet = codec.encode(_sample()).replace(b"siglip2-base", b"siglip2-base")
        # Corrupt the face embedding base64 only.
        broken = packet.replace(b"<pictopy:Embedding>", b"<pictopy:Embedding>!!")
        decoded = codec.decode(broken)
        assert decoded is not None
        assert decoded.tags == ["person", "dog"]
        assert decoded.albums == ["Trip", "Family"]

    def test_non_pictopy_packet_returns_none(self):
        packet = (
            b'<x:xmpmeta xmlns:x="adobe:ns:meta/"><rdf:RDF '
            b'xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
            b'<rdf:Description rdf:about=""/></rdf:RDF></x:xmpmeta>'
        )
        assert PictoPyXmpCodec().decode(packet) is None

    def test_rejects_entity_declarations(self):
        bomb = b'<!DOCTYPE x [<!ENTITY a "aaaa">]><x:xmpmeta xmlns:x="adobe:ns:meta/"/>'
        assert PictoPyXmpCodec().decode(bomb) is None

    def test_foreign_xmp_is_preserved_and_ours_replaced(self):
        codec = PictoPyXmpCodec()
        foreign = (
            b'<x:xmpmeta xmlns:x="adobe:ns:meta/"><rdf:RDF '
            b'xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
            b'<rdf:Description rdf:about="" xmlns:dc="http://purl.org/dc/elements/1.1/">'
            b"<dc:creator>Someone</dc:creator></rdf:Description></rdf:RDF></x:xmpmeta>"
        )
        first = codec.encode(PictoPyMetadata(tags=["old"]), existing=foreign)
        second = codec.encode(PictoPyMetadata(tags=["new"]), existing=first)
        assert b"Someone" in second
        assert second.count(NS_PICTOPY.encode() + b'"') == 1
        decoded = codec.decode(second)
        assert decoded is not None
        assert decoded.tags == ["new"]


class TestPngContainer:
    def test_write_then_read(self, png):
        meta = _sample()
        assert write_image_metadata(png, meta) is True
        assert read_image_metadata(png) == meta

    def test_pixels_and_idat_are_untouched(self, png):
        before_pixels = Image.open(png).tobytes()
        before_idat = _idat_bytes(png)
        write_image_metadata(png, _sample())
        assert Image.open(png).tobytes() == before_pixels
        assert _idat_bytes(png) == before_idat
        Image.open(png).verify()

    def test_rewrite_replaces_not_appends(self, png):
        write_image_metadata(png, _sample())
        once = open(png, "rb").read()
        write_image_metadata(png, _sample())
        assert open(png, "rb").read() == once

    def test_pillow_sees_the_packet(self, png):
        write_image_metadata(png, PictoPyMetadata(tags=["cat"]))
        assert "pictopy" in Image.open(png).info["XML:com.adobe.xmp"]

    def test_compressed_itxt_is_readable(self, png):
        packet = PictoPyXmpCodec().encode(PictoPyMetadata(tags=["z"]))
        body = b"XML:com.adobe.xmp\x00\x01\x00\x00\x00" + zlib.compress(packet)
        data = bytearray(open(png, "rb").read())
        idat = data.index(b"IDAT") - 4
        chunk = (
            struct.pack(">I", len(body))
            + b"iTXt"
            + body
            + struct.pack(">I", zlib.crc32(b"iTXt" + body))
        )
        open(png, "wb").write(bytes(data[:idat]) + chunk + bytes(data[idat:]))
        decoded = read_image_metadata(png)
        assert decoded is not None
        assert decoded.tags == ["z"]

    def test_unsupported_format_is_a_noop(self, tmp_path):
        path = tmp_path / "a.jpg"
        Image.new("RGB", (8, 8)).save(path)
        before = path.read_bytes()
        assert is_xmp_supported(str(path)) is False
        assert write_image_metadata(str(path), _sample()) is False
        assert read_image_metadata(str(path)) is None
        assert path.read_bytes() == before

    def test_truncated_png_leaves_file_alone(self, png):
        data = open(png, "rb").read()[:-30]
        open(png, "wb").write(data)
        with pytest.raises(PngFormatError):
            PngContainer().write_xmp(png, b"<x/>")
        assert open(png, "rb").read() == data
        assert read_image_metadata(png) is None

    def test_no_temp_files_left_behind(self, png, tmp_path):
        write_image_metadata(png, _sample())
        assert [p.name for p in tmp_path.iterdir()] == ["a.png"]
