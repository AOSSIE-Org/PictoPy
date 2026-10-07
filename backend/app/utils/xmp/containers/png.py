import os
import struct
import tempfile
import zlib
from typing import Iterator, Optional, Tuple

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
# The keyword the XMP spec reserves for the packet in a PNG iTXt chunk.
XMP_KEYWORD = b"XML:com.adobe.xmp"
# Guards against a corrupt length field making us read the whole file as one chunk.
MAX_CHUNK_BYTES = 256 * 1024 * 1024


class PngFormatError(ValueError):
    pass


def _iter_chunks(data: bytes) -> Iterator[Tuple[bytes, bytes, bytes]]:
    """Yield (type, body, raw bytes) for every chunk, validating lengths."""
    if not data.startswith(PNG_SIGNATURE):
        raise PngFormatError("not a PNG file")
    pos = len(PNG_SIGNATURE)
    while pos + 12 <= len(data):
        (length,) = struct.unpack(">I", data[pos : pos + 4])
        end = pos + 12 + length
        if length > MAX_CHUNK_BYTES or end > len(data):
            raise PngFormatError("truncated or oversized chunk")
        yield data[pos + 4 : pos + 8], data[pos + 8 : pos + 8 + length], data[pos:end]
        pos = end


def _make_chunk(chunk_type: bytes, body: bytes) -> bytes:
    crc = zlib.crc32(chunk_type + body) & 0xFFFFFFFF
    return struct.pack(">I", len(body)) + chunk_type + body + struct.pack(">I", crc)


def _is_xmp_chunk(chunk_type: bytes, body: bytes) -> bool:
    return chunk_type == b"iTXt" and body.startswith(XMP_KEYWORD + b"\x00")


def _parse_itxt_text(body: bytes) -> Optional[bytes]:
    """Text of an iTXt body: keyword\0 flag method lang\0 translated\0 text."""
    rest = body[len(XMP_KEYWORD) + 1 :]
    if len(rest) < 2:
        return None
    compressed, _method = rest[0], rest[1]
    parts = rest[2:].split(b"\x00", 2)
    if len(parts) < 3:
        return None
    text = parts[2]
    return zlib.decompress(text) if compressed else text


class PngContainer:
    def supports(self, path: str) -> bool:
        try:
            with open(path, "rb") as f:
                return f.read(len(PNG_SIGNATURE)) == PNG_SIGNATURE
        except OSError:
            return False

    def read_xmp(self, path: str) -> Optional[bytes]:
        with open(path, "rb") as f:
            data = f.read()
        for chunk_type, body, _raw in _iter_chunks(data):
            if _is_xmp_chunk(chunk_type, body):
                return _parse_itxt_text(body)
        return None

    def write_xmp(self, path: str, packet: bytes) -> None:
        with open(path, "rb") as f:
            data = f.read()

        # Uncompressed so the packet stays readable with plain tools.
        body = XMP_KEYWORD + b"\x00" + b"\x00\x00" + b"\x00" + b"\x00" + packet
        new_chunk = _make_chunk(b"iTXt", body)

        out = bytearray(PNG_SIGNATURE)
        inserted = False
        for chunk_type, chunk_body, raw in _iter_chunks(data):
            if _is_xmp_chunk(chunk_type, chunk_body):
                continue
            # iTXt may sit anywhere between IHDR and IEND; before IDAT keeps it
            # readable without scanning the pixel data.
            if chunk_type == b"IDAT" and not inserted:
                out += new_chunk
                inserted = True
            out += raw  # untouched, so pixel data stays byte-identical
        if not inserted:
            raise PngFormatError("no IDAT chunk found")

        _atomic_replace(path, bytes(out))


def _atomic_replace(path: str, content: bytes) -> None:
    """Write beside the target then rename, so a crash never leaves half a PNG."""
    directory = os.path.dirname(os.path.abspath(path))
    fd, tmp_path = tempfile.mkstemp(dir=directory, suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as tmp:
            tmp.write(content)
        # Keep the original permissions; mkstemp creates the file 0600.
        try:
            os.chmod(tmp_path, os.stat(path).st_mode & 0o777)
        except OSError:
            pass
        os.replace(tmp_path, path)
    except BaseException:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise
