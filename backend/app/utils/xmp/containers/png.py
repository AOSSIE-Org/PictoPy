import os
import struct
import tempfile
import zlib
from typing import BinaryIO, Iterator, List, Optional, Tuple

from .base import (
    MAX_PACKET_BYTES,
    STREAM_BLOCK_BYTES,
    FileChangedError,
    TransformedStream,
    XmpTransform,
)

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
# The keyword the XMP spec reserves for the packet in a PNG iTXt chunk.
XMP_KEYWORD = b"XML:com.adobe.xmp"
# Guards against a corrupt length field making us read the whole file as one chunk.
MAX_CHUNK_BYTES = 256 * 1024 * 1024


class PngFormatError(ValueError):
    pass


Chunk = Tuple[bytes, bytes, bytes]  # (type, body, raw bytes)


def _split_chunks(data: bytes) -> Tuple[List[Chunk], bytes]:
    """Chunks up to and including IEND, plus any bytes after it."""
    if not data.startswith(PNG_SIGNATURE):
        raise PngFormatError("not a PNG file")
    chunks: List[Chunk] = []
    pos = len(PNG_SIGNATURE)
    while True:
        if pos + 12 > len(data):
            raise PngFormatError("missing IEND chunk")
        (length,) = struct.unpack(">I", data[pos : pos + 4])
        end = pos + 12 + length
        if length > MAX_CHUNK_BYTES or end > len(data):
            raise PngFormatError("truncated or oversized chunk")
        chunk_type = data[pos + 4 : pos + 8]
        chunks.append((chunk_type, data[pos + 8 : pos + 8 + length], data[pos:end]))
        pos = end
        if chunk_type == b"IEND":
            # Some tools append data after IEND; carry it over untouched.
            return chunks, data[pos:]


def _make_chunk(chunk_type: bytes, body: bytes) -> bytes:
    crc = zlib.crc32(chunk_type + body) & 0xFFFFFFFF
    return struct.pack(">I", len(body)) + chunk_type + body + struct.pack(">I", crc)


def _is_xmp_chunk(chunk_type: bytes, body: bytes) -> bool:
    return chunk_type == b"iTXt" and body.startswith(XMP_KEYWORD + b"\x00")


def _parse_itxt_text(body: bytes) -> Optional[bytes]:
    """Text of an iTXt body: keyword\\0 flag method lang\\0 translated\\0 text."""
    rest = body[len(XMP_KEYWORD) + 1 :]
    if len(rest) < 2:
        return None
    compressed = rest[0]
    parts = rest[2:].split(b"\x00", 2)
    if len(parts) < 3:
        return None
    text = parts[2]
    if not compressed:
        return text
    # Bounded, so a tiny chunk cannot inflate into gigabytes.
    inflater = zlib.decompressobj()
    try:
        packet = inflater.decompress(text, MAX_PACKET_BYTES)
    except zlib.error as e:
        raise PngFormatError(f"corrupt compressed XMP: {e}") from e
    if inflater.unconsumed_tail:
        raise PngFormatError("compressed XMP too large")
    return packet


def _read_exact(f: BinaryIO, size: int) -> bytes:
    data = f.read(size)
    if len(data) != size:
        raise PngFormatError("truncated chunk")
    return data


def _xmp_chunk(packet: bytes) -> bytes:
    # Uncompressed so the packet stays readable with plain tools.
    body = XMP_KEYWORD + b"\x00" + b"\x00\x00" + b"\x00" + b"\x00" + packet
    return _make_chunk(b"iTXt", body)


Edit = Tuple[int, int, bytes]  # (offset, bytes replaced, replacement)


def _plan_xmp_edits(f: BinaryIO, transform: XmpTransform) -> List[Edit]:
    """Where the XMP chunks are and what replaces each; reads only their bodies."""
    if f.read(len(PNG_SIGNATURE)) != PNG_SIGNATURE:
        raise PngFormatError("not a PNG file")
    edits: List[Edit] = []
    prefix_len = len(XMP_KEYWORD) + 1
    while True:
        offset = f.tell()
        header = f.read(8)
        if len(header) < 8:
            return edits
        length, chunk_type = struct.unpack(">I", header[:4])[0], header[4:]
        if chunk_type == b"IEND":
            return edits
        if chunk_type != b"iTXt" or length < prefix_len:
            f.seek(length + 4, os.SEEK_CUR)
            continue

        prefix = _read_exact(f, prefix_len)
        if not _is_xmp_chunk(chunk_type, prefix):
            f.seek(length - prefix_len + 4, os.SEEK_CUR)
            continue

        total = 12 + length
        if length > MAX_PACKET_BYTES:
            # Too large to inspect, so it cannot be cleaned; drop it.
            f.seek(length - prefix_len + 4, os.SEEK_CUR)
            edits.append((offset, total, b""))
            continue

        body = prefix + _read_exact(f, length - prefix_len)
        f.seek(4, os.SEEK_CUR)
        try:
            packet = _parse_itxt_text(body)
        except PngFormatError:
            packet = None
        replacement = transform(packet) if packet is not None else None
        if replacement is None:
            edits.append((offset, total, b""))
        elif replacement != packet:
            edits.append((offset, total, _xmp_chunk(replacement)))


def _copy(f: BinaryIO, count: int) -> Iterator[bytes]:
    while count > 0:
        block = f.read(min(STREAM_BLOCK_BYTES, count))
        if not block:
            return
        count -= len(block)
        yield block


class PngContainer:
    def supports(self, path: str) -> bool:
        try:
            with open(path, "rb") as f:
                return f.read(len(PNG_SIGNATURE)) == PNG_SIGNATURE
        except OSError:
            return False

    def read_xmp(self, path: str) -> Optional[bytes]:
        # Walks chunk headers and seeks past bodies, so the pixel data of a
        # large PNG is never read just to check its metadata.
        with open(path, "rb") as f:
            if f.read(len(PNG_SIGNATURE)) != PNG_SIGNATURE:
                raise PngFormatError("not a PNG file")
            while True:
                header = f.read(8)
                if len(header) < 8:
                    return None
                length, chunk_type = struct.unpack(">I", header[:4])[0], header[4:]
                if chunk_type == b"IEND":
                    return None
                if chunk_type == b"iTXt" and length <= MAX_PACKET_BYTES:
                    body = _read_exact(f, length)
                    f.seek(4, os.SEEK_CUR)
                    if _is_xmp_chunk(chunk_type, body):
                        return _parse_itxt_text(body)
                else:
                    f.seek(length + 4, os.SEEK_CUR)

    def write_xmp(self, path: str, packet: bytes) -> None:
        with open(path, "rb") as f:
            before = os.fstat(f.fileno())
            data = f.read()

        chunks, trailing = _split_chunks(data)
        new_chunk = _xmp_chunk(packet)

        out = bytearray(PNG_SIGNATURE)
        inserted = False
        for chunk_type, chunk_body, raw in chunks:
            if _is_xmp_chunk(chunk_type, chunk_body):
                continue
            # iTXt may sit anywhere between IHDR and IEND; before IDAT lets
            # read_xmp find it without seeking through the pixel data.
            if chunk_type == b"IDAT" and not inserted:
                out += new_chunk
                inserted = True
            out += raw  # untouched, so pixel data stays byte-identical
        if not inserted:
            raise PngFormatError("no IDAT chunk found")
        out += trailing

        _atomic_replace(path, bytes(out), before)

    def stream_with_xmp(self, path: str, transform: XmpTransform) -> TransformedStream:
        # One handle for planning and streaming, so the length promised up
        # front describes exactly the bytes that are sent.
        f = open(path, "rb")
        try:
            size = os.fstat(f.fileno()).st_size
            edits = _plan_xmp_edits(f, transform)
        except BaseException:
            f.close()
            raise

        length = size + sum(len(new) - old for _offset, old, new in edits)

        def chunks() -> Iterator[bytes]:
            try:
                f.seek(0)
                pos = 0
                for offset, old, new in edits:
                    yield from _copy(f, offset - pos)
                    if new:
                        yield new
                    f.seek(offset + old)
                    pos = offset + old
                # Pixel data and anything after IEND pass through untouched.
                yield from _copy(f, size - pos)
            finally:
                f.close()

        return TransformedStream(length=length, chunks=chunks())


def _atomic_replace(path: str, content: bytes, before: os.stat_result) -> None:
    """Write beside the target then rename, so a crash never leaves half a PNG."""
    directory = os.path.dirname(os.path.abspath(path))
    fd, tmp_path = tempfile.mkstemp(dir=directory, suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as tmp:
            tmp.write(content)
            tmp.flush()
            os.fsync(tmp.fileno())
        # Keep the original permissions; mkstemp creates the file 0600.
        try:
            os.chmod(tmp_path, before.st_mode & 0o777)
        except OSError:
            pass

        # Someone else saved the file while we built ours; theirs wins.
        now = os.stat(path)
        if (now.st_size, now.st_mtime_ns) != (before.st_size, before.st_mtime_ns):
            raise FileChangedError(f"{path} changed during metadata write")

        os.replace(tmp_path, path)
    except BaseException:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise

    # PNG capture dates fall back to mtime, so a new one would move the photo
    # in the timeline.
    os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns))
