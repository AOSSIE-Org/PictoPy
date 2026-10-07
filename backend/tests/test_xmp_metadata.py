import gc
import io
import os
import struct
import tracemalloc
import zlib

import numpy as np
import pytest
from PIL import Image

from app.utils.xmp import (
    EmbeddingRecord,
    FaceRecord,
    PictoPyMetadata,
    SemanticTag,
    WriteOutcome,
    is_xmp_supported,
    open_without_pictopy,
    read_image_metadata,
    write_image_metadata,
)
from app.utils.xmp.codec import PictoPyXmpCodec
from app.utils.xmp.containers import png as png_module
from app.utils.xmp.containers.base import STREAM_BLOCK_BYTES, FileChangedError
from app.utils.xmp.containers.png import PngContainer, PngFormatError

RDF_OPEN = (
    b'<x:xmpmeta xmlns:x="adobe:ns:meta/"><rdf:RDF '
    b'xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
)
RDF_CLOSE = b"</rdf:RDF></x:xmpmeta>"


def _sample() -> PictoPyMetadata:
    # Deliberately float64 values that float32 cannot represent exactly.
    return PictoPyMetadata(
        tags=["person", "dog"],
        semantic_tags=[SemanticTag("beach & sunset", 0.3141592653589793)],
        faces=[
            FaceRecord(
                embedding=[0.1, -1.7, 3.3],
                bbox={"y": 20, "x": 10, "width": 30.5, "height": 40},
                confidence=0.98,
                cluster_name="Alice <A>",
            ),
            FaceRecord(embedding=[1.0, 2.0, 3.0]),
        ],
        image_embedding=EmbeddingRecord("siglip2-base", [0.2, 0.7]),
        favourite=True,
        albums=["Trip", "Family"],
        models={"face_embedding": "FaceNet_128D", "semantic_vocabulary": "abc"},
        width=64,
        height=64,
    )


def _itxt(packet: bytes, compressed: bool = False) -> bytes:
    text = zlib.compress(packet) if compressed else packet
    body = b"XML:com.adobe.xmp\x00" + bytes([int(compressed), 0]) + b"\x00\x00" + text
    crc = struct.pack(">I", zlib.crc32(b"iTXt" + body))
    return struct.pack(">I", len(body)) + b"iTXt" + body + crc


def _insert_chunk(path: str, chunk: bytes, before: bytes = b"IDAT") -> None:
    with open(path, "rb") as f:
        data = f.read()
    at = data.index(before) - 4
    with open(path, "wb") as f:
        f.write(data[:at] + chunk + data[at:])


def _read(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()


def _idat_bytes(path: str) -> bytes:
    data, out, pos = _read(path), b"", 8
    while pos < len(data):
        (length,) = struct.unpack(">I", data[pos : pos + 4])
        if data[pos + 4 : pos + 8] == b"IDAT":
            out += data[pos + 8 : pos + 8 + length]
        pos += 12 + length
    return out


@pytest.fixture
def png(tmp_path):
    path = tmp_path / "a.png"
    rng = np.random.default_rng(0)
    Image.fromarray(rng.integers(0, 256, (64, 64, 3), dtype=np.uint8)).save(path)
    # A past mtime, so "kept" cannot pass by the write landing in the same tick.
    os.utime(path, ns=(1_500_000_000_000_000_000, 1_500_000_000_000_000_000))
    return str(path)


class TestCodec:
    def test_round_trip_is_float32_exact_and_digest_stable(self):
        codec = PictoPyXmpCodec()
        decoded = codec.decode(codec.encode(_sample()))
        assert decoded is not None
        assert decoded.tags == ["person", "dog"]
        assert decoded.albums == ["Trip", "Family"]
        assert decoded.models == _sample().models
        assert decoded.faces[0].bbox == _sample().faces[0].bbox
        assert decoded.faces[0].cluster_name == "Alice <A>"
        assert decoded.semantic_tags == _sample().semantic_tags
        assert np.allclose(decoded.faces[0].embedding, [0.1, -1.7, 3.3])
        # Change detection compares digests, so float32 rounding must not
        # make the database's float64 values look like a change.
        assert codec.digest(decoded) == codec.digest(_sample())

    def test_digest_tracks_content(self):
        codec = PictoPyXmpCodec()
        changed = _sample()
        changed.faces[0].cluster_name = "Bob"
        assert codec.digest(changed) != codec.digest(_sample())

    def test_empty_metadata_round_trips(self):
        codec = PictoPyXmpCodec()
        assert codec.decode(codec.encode(PictoPyMetadata())) == PictoPyMetadata()

    def test_newer_schema_version_is_not_decoded(self):
        codec = PictoPyXmpCodec()
        assert codec.decode(codec.encode(PictoPyMetadata(schema_version=999))) is None

    def test_malformed_section_does_not_drop_others(self):
        codec = PictoPyXmpCodec()
        packet = codec.encode(_sample())
        broken = packet.replace(b"<pictopy:Embedding>", b"<pictopy:Embedding>!!", 1)
        assert broken != packet
        decoded = codec.decode(broken)
        assert decoded is not None
        assert decoded.faces == []
        assert decoded.tags == ["person", "dog"]
        assert decoded.image_embedding is not None

    def test_non_pictopy_packet_returns_none(self):
        packet = RDF_OPEN + b'<rdf:Description rdf:about=""/>' + RDF_CLOSE
        assert PictoPyXmpCodec().decode(packet) is None

    def test_rejects_entity_declarations(self):
        bomb = b'<!DOCTYPE x [<!ENTITY a "aaaa">]><x:xmpmeta xmlns:x="adobe:ns:meta/"/>'
        assert PictoPyXmpCodec().decode(bomb) is None

    def test_reads_attribute_form(self):
        packet = (
            RDF_OPEN
            + b'<rdf:Description rdf:about="" xmlns:pictopy="https://pictopy.app/ns/1.0/"'
            + b' pictopy:SchemaVersion="1" pictopy:Favourite="true"/>'
            + RDF_CLOSE
        )
        decoded = PictoPyXmpCodec().decode(packet)
        assert decoded is not None
        assert decoded.favourite is True

    def test_foreign_description_is_preserved_and_ours_replaced(self):
        codec = PictoPyXmpCodec()
        foreign = (
            RDF_OPEN
            + b'<rdf:Description rdf:about="" xmlns:dc="http://purl.org/dc/elements/1.1/">'
            + b"<dc:creator>Someone</dc:creator></rdf:Description>"
            + RDF_CLOSE
        )
        first = codec.encode(PictoPyMetadata(tags=["old"]), existing=foreign)
        second = codec.encode(PictoPyMetadata(tags=["new"]), existing=first)
        assert b"Someone" in second
        assert second.count(b"<pictopy:SchemaVersion>") == 1
        decoded = codec.decode(second)
        assert decoded is not None
        assert decoded.tags == ["new"]

    def test_foreign_properties_merged_into_our_description_survive(self):
        # exiftool and others merge every namespace into one description.
        codec = PictoPyXmpCodec()
        merged = codec.encode(PictoPyMetadata(tags=["a"])).replace(
            b'<rdf:Description rdf:about="">',
            b'<rdf:Description rdf:about="" xmlns:dc="http://purl.org/dc/elements/1.1/">'
            b"<dc:creator>Someone</dc:creator>",
        )
        assert b"Someone" in merged
        rewritten = codec.encode(PictoPyMetadata(tags=["b"]), existing=merged)
        assert b"Someone" in rewritten
        assert b"<rdf:li>a</rdf:li>" not in rewritten


class TestPngWrites:
    def test_write_then_read(self, png):
        assert write_image_metadata(png, _sample()) is WriteOutcome.WRITTEN
        decoded = read_image_metadata(png)
        assert decoded is not None
        assert decoded.tags == _sample().tags

    def test_pixels_and_idat_are_untouched(self, png):
        before_pixels = Image.open(png).tobytes()
        before_idat = _idat_bytes(png)
        write_image_metadata(png, _sample())
        assert Image.open(png).tobytes() == before_pixels
        assert _idat_bytes(png) == before_idat
        Image.open(png).verify()

    def test_mtime_is_kept(self, png):
        before = os.stat(png).st_mtime_ns
        write_image_metadata(png, _sample())
        assert os.stat(png).st_mtime_ns == before

    def test_identical_data_is_not_rewritten(self, png):
        write_image_metadata(png, _sample())
        once = _read(png)
        assert write_image_metadata(png, _sample()) is WriteOutcome.UNCHANGED
        assert _read(png) == once

    def test_changed_data_replaces_rather_than_appends(self, png):
        write_image_metadata(png, _sample())
        changed = _sample()
        changed.favourite = False
        assert write_image_metadata(png, changed) is WriteOutcome.WRITTEN
        assert _read(png).count(b"XML:com.adobe.xmp") == 1
        decoded = read_image_metadata(png)
        assert decoded is not None
        assert decoded.favourite is False

    def test_newer_schema_in_file_is_left_alone(self, png):
        _insert_chunk(
            png, _itxt(PictoPyXmpCodec().encode(PictoPyMetadata(schema_version=2)))
        )
        before = _read(png)
        assert write_image_metadata(png, _sample()) is WriteOutcome.NEWER_SCHEMA
        assert _read(png) == before

    def test_trailing_bytes_after_iend_survive(self, png):
        with open(png, "ab") as f:
            f.write(b"tail")
        write_image_metadata(png, _sample())
        assert _read(png).endswith(b"IEND\xaeB`\x82tail")

    def test_file_changed_mid_write_is_not_clobbered(self, png, monkeypatch):
        real_mkstemp = png_module.tempfile.mkstemp

        def mkstemp_then_user_saves(*args, **kwargs):
            with open(png, "ab") as f:
                f.write(b"user edit")
            return real_mkstemp(*args, **kwargs)

        monkeypatch.setattr(png_module.tempfile, "mkstemp", mkstemp_then_user_saves)
        with pytest.raises(FileChangedError):
            write_image_metadata(png, _sample())
        assert _read(png).endswith(b"user edit")
        assert [p.name for p in os.scandir(os.path.dirname(png))] == ["a.png"]

    def test_unsupported_format_is_a_noop(self, tmp_path):
        path = tmp_path / "a.jpg"
        Image.new("RGB", (8, 8)).save(path)
        before = path.read_bytes()
        assert is_xmp_supported(str(path)) is False
        assert write_image_metadata(str(path), _sample()) is WriteOutcome.UNSUPPORTED
        assert read_image_metadata(str(path)) is None
        assert path.read_bytes() == before

    def test_truncated_png_is_refused(self, png):
        data = _read(png)[:-30]
        with open(png, "wb") as f:
            f.write(data)
        with pytest.raises(PngFormatError):
            PngContainer().write_xmp(png, b"<x/>")
        assert _read(png) == data

    def test_no_temp_files_left_behind(self, png, tmp_path):
        write_image_metadata(png, _sample())
        assert [p.name for p in tmp_path.iterdir()] == ["a.png"]


class TestPngReads:
    def test_pillow_sees_the_packet(self, png):
        write_image_metadata(png, PictoPyMetadata(tags=["cat"]))
        assert "pictopy" in Image.open(png).info["XML:com.adobe.xmp"]

    def test_compressed_itxt_is_readable(self, png):
        _insert_chunk(
            png,
            _itxt(
                PictoPyXmpCodec().encode(PictoPyMetadata(tags=["z"])), compressed=True
            ),
        )
        decoded = read_image_metadata(png)
        assert decoded is not None
        assert decoded.tags == ["z"]

    def test_packet_after_idat_is_found(self, png):
        packet = PictoPyXmpCodec().encode(PictoPyMetadata(tags=["late"]))
        _insert_chunk(png, _itxt(packet), before=b"IEND")
        decoded = read_image_metadata(png)
        assert decoded is not None
        assert decoded.tags == ["late"]

    def test_corrupt_compressed_packet_reads_as_absent(self, png):
        packet = PictoPyXmpCodec().encode(PictoPyMetadata(tags=["z"]))
        chunk = bytearray(_itxt(packet, compressed=True))
        chunk[-8:-4] = b"XXXX"  # break the zlib checksum, not the CRC
        _insert_chunk(png, bytes(chunk))
        with pytest.raises(PngFormatError, match="corrupt"):
            PngContainer().read_xmp(png)
        assert read_image_metadata(png) is None

    def test_decompression_is_bounded(self, png, monkeypatch):
        packet = PictoPyXmpCodec().encode(PictoPyMetadata(tags=["z"] * 500))
        monkeypatch.setattr(png_module, "MAX_PACKET_BYTES", 1024)
        _insert_chunk(png, _itxt(packet, compressed=True))
        with pytest.raises(PngFormatError, match="too large"):
            PngContainer().read_xmp(png)
        assert read_image_metadata(png) is None


FOREIGN_DESCRIPTION = (
    b'<rdf:Description rdf:about="" xmlns:dc="http://purl.org/dc/elements/1.1/">'
    b"<dc:creator>Someone</dc:creator></rdf:Description>"
)


def _chunk(chunk_type: bytes, body: bytes) -> bytes:
    crc = struct.pack(">I", zlib.crc32(chunk_type + body))
    return struct.pack(">I", len(body)) + chunk_type + body + crc


def _served(path: str) -> bytes:
    stream = open_without_pictopy(path)
    assert stream is not None
    data = b"".join(stream.chunks)
    assert len(data) == stream.length
    return data


def _pixels(data: bytes) -> bytes:
    return Image.open(io.BytesIO(data)).tobytes()


class TestCodecStrip:
    def test_foreign_only_packet_is_returned_untouched(self):
        packet = RDF_OPEN + FOREIGN_DESCRIPTION + RDF_CLOSE
        assert PictoPyXmpCodec().strip(packet) is packet

    def test_pictopy_only_packet_strips_to_nothing(self):
        codec = PictoPyXmpCodec()
        assert codec.strip(codec.encode(_sample())) is None

    def test_merged_description_keeps_foreign_properties(self):
        codec = PictoPyXmpCodec()
        merged = codec.encode(_sample()).replace(
            b'<rdf:Description rdf:about="">',
            b'<rdf:Description rdf:about="" xmlns:dc="http://purl.org/dc/elements/1.1/">'
            b"<dc:creator>Someone</dc:creator>",
        )
        stripped = codec.strip(merged)
        assert stripped is not None
        assert b"Someone" in stripped
        assert b"pictopy" not in stripped

    def test_pictopy_data_is_removed_and_pixels_kept(self, png):
        write_image_metadata(png, _sample())
        on_disk, mtime = _read(png), os.stat(png).st_mtime_ns

        served = _served(png)
        assert b"pictopy" not in served
        assert b"XML:com.adobe.xmp" not in served
        assert _pixels(served) == _pixels(on_disk)
        Image.open(io.BytesIO(served)).verify()
        # The original is never modified.
        assert _read(png) == on_disk
        assert os.stat(png).st_mtime_ns == mtime

    def test_other_tools_xmp_survives(self, png):
        _insert_chunk(png, _itxt(RDF_OPEN + FOREIGN_DESCRIPTION + RDF_CLOSE))
        write_image_metadata(png, _sample())
        assert b"pictopy" in _read(png)

        served = _served(png)
        assert b"pictopy" not in served
        assert b"<dc:creator>Someone</dc:creator>" in served
        assert _pixels(served) == _pixels(_read(png))

    def test_other_metadata_chunks_survive(self, png):
        _insert_chunk(png, _chunk(b"tEXt", b"Author\x00Someone"))
        _insert_chunk(png, _chunk(b"eXIf", b"MM\x00*fake-exif"))
        write_image_metadata(png, _sample())
        with open(png, "ab") as f:
            f.write(b"tail")

        served = _served(png)
        assert b"Author\x00Someone" in served
        assert b"MM\x00*fake-exif" in served
        assert served.endswith(b"tail")

    def test_file_without_pictopy_data_is_served_byte_identical(self, png):
        _insert_chunk(png, _itxt(RDF_OPEN + FOREIGN_DESCRIPTION + RDF_CLOSE))
        assert _served(png) == _read(png)

    def test_packet_after_idat_is_also_stripped(self, png):
        packet = PictoPyXmpCodec().encode(_sample())
        _insert_chunk(png, _itxt(packet), before=b"IEND")
        assert b"pictopy" not in _served(png)

    def test_compressed_packet_is_stripped(self, png):
        packet = PictoPyXmpCodec().encode(_sample())
        _insert_chunk(png, _itxt(packet, compressed=True))
        served = _served(png)
        assert b"XML:com.adobe.xmp" not in served
        assert _pixels(served) == _pixels(_read(png))

    def test_non_png_is_left_to_the_caller(self, tmp_path):
        path = tmp_path / "a.jpg"
        Image.new("RGB", (8, 8)).save(path)
        assert open_without_pictopy(str(path)) is None

    def test_memory_does_not_grow_with_file_size(self, png):
        write_image_metadata(png, _sample())
        # A 32 MB ancillary chunk stands in for a large photo's pixel data.
        _insert_chunk(png, _chunk(b"prVt", b"\x00" * (32 * 1024 * 1024)))
        stream = open_without_pictopy(png)
        assert stream is not None

        gc.collect()
        tracemalloc.start()
        try:
            largest = 0
            for block in stream.chunks:
                largest = max(largest, len(block))
            _, peak = tracemalloc.get_traced_memory()
        finally:
            tracemalloc.stop()
        assert largest <= STREAM_BLOCK_BYTES
        assert peak < 2 * 1024 * 1024
