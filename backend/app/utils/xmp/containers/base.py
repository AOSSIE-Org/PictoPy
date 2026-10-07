from dataclasses import dataclass
from typing import Callable, Iterator, Optional, Protocol

# Far above anything PictoPy writes; refuses hostile or corrupt packets early.
MAX_PACKET_BYTES = 64 * 1024 * 1024
# Matches Starlette's FileResponse, so streaming costs what a plain send does.
STREAM_BLOCK_BYTES = 64 * 1024

# Maps an XMP packet to its replacement; None drops the packet entirely.
XmpTransform = Callable[[bytes], Optional[bytes]]


class FileChangedError(OSError):
    """The file changed between reading it and replacing it."""


@dataclass
class TransformedStream:
    """A file's bytes with its XMP rewritten, produced without loading the file."""

    length: int
    chunks: Iterator[bytes]


class MetadataContainer(Protocol):
    """Where an XMP packet lives inside one image format.

    Writes must leave the pixel data byte-for-byte untouched and keep the
    file's modification time.
    """

    def supports(self, path: str) -> bool: ...

    def read_xmp(self, path: str) -> Optional[bytes]: ...

    def write_xmp(self, path: str, packet: bytes) -> None: ...

    def stream_with_xmp(self, path: str, transform: XmpTransform) -> TransformedStream:
        """Stream the file with every XMP packet passed through `transform`.

        Memory must stay bounded by the packet size, never the file size. A
        packet that cannot be read must be dropped rather than sent unchanged.
        """
        ...
