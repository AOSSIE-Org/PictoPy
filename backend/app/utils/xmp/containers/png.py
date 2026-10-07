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


def _contains(f: BinaryIO, count: int, marker: bytes) -> bool:
    """Whether the next `count` bytes contain `marker`, read in bounded blocks."""
    tail = b""
    found = False
    while count > 0:
        block = f.read(min(STREAM_BLOCK_BYTES, count))
        if not block:
            raise PngFormatError("truncated chunk")
        count -= len(block)
        window = tail + block
        found = found or marker in window
        # Carry over from the window, not the block: with blocks shorter than
        # the marker, a match can span more than two of them.
        tail = window[-(len(marker) - 1) :] if len(marker) > 1 else b""
    return found


def _plan_xmp_edits(f: BinaryIO, transform: XmpTransform, marker: bytes) -> List[Edit]:
    """Where the XMP chunks are and what replaces each; reads only their bodies.

    A chunk that cannot be passed through `transform` is dropped only when it
    may hold `marker`; anything provably free of it is kept untouched.
    """
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
        drop = (offset, total, b"")
        if length > MAX_PACKET_BYTES:
            # Too large to rewrite; scan it instead of holding it.
            flag = _read_exact(f, 1)
            compressed = flag != b"\x00"
            holds = _contains(f, length - prefix_len - 1, marker)
            f.seek(4, os.SEEK_CUR)
            if compressed or holds:
                edits.append(drop)
            continue

        body = prefix + _read_exact(f, length - prefix_len)
        f.seek(4, os.SEEK_CUR)
        try:
            packet = _parse_itxt_text(body)
        except PngFormatError:
            packet = None
        if packet is None:
            # Unreadable chunk: compressed bytes cannot be inspected, so keep
            # it only if it is plain text without our marker.
            compressed = len(body) > prefix_len and body[prefix_len] != 0
            if compressed or marker in body:
                edits.append(drop)
            continue

        replacement = transform(packet)
        if replacement is None:
            edits.append(drop)
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
        """The file's XMP packet, or None if it has none.

        Raises PngFormatError for XMP it cannot read, or more than one packet:
        write_xmp replaces every XMP chunk, so a caller must not write over
        packets it could not see. Walks chunk headers and seeks past bodies, so
        a large PNG's pixel data is never read.
        """
        prefix_len = len(XMP_KEYWORD) + 1
        found: Optional[bytes] = None
        with open(path, "rb") as f:
            if f.read(len(PNG_SIGNATURE)) != PNG_SIGNATURE:
                raise PngFormatError("not a PNG file")
            while True:
                header = f.read(8)
                if len(header) < 8 or header[4:] == b"IEND":
                    return found
                length, chunk_type = struct.unpack(">I", header[:4])[0], header[4:]
                if chunk_type != b"iTXt" or length < prefix_len:
                    f.seek(length + 4, os.SEEK_CUR)
                    continue
                prefix = _read_exact(f, prefix_len)
                if not _is_xmp_chunk(chunk_type, prefix):
                    f.seek(length - prefix_len + 4, os.SEEK_CUR)
                    continue
                if found is not None:
                    raise PngFormatError("more than one XMP packet")
                if length > MAX_PACKET_BYTES:
                    raise PngFormatError("XMP packet too large to read")
                body = prefix + _read_exact(f, length - prefix_len)
                f.seek(4, os.SEEK_CUR)
                found = _parse_itxt_text(body)
                if found is None:
                    raise PngFormatError("malformed XMP chunk")

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

    def stream_with_xmp(
        self, path: str, transform: XmpTransform, marker: bytes
    ) -> TransformedStream:
        # One handle for planning and streaming, so the length promised up
        # front describes exactly the bytes that are sent.
        f = open(path, "rb")
        try:
            stat = os.fstat(f.fileno())
            size = stat.st_size
            edits = _plan_xmp_edits(f, transform, marker)
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

        return TransformedStream(length=length, chunks=chunks(), source_stat=stat)


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
