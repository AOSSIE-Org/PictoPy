from typing import Optional, Protocol

# Far above anything PictoPy writes; refuses hostile or corrupt packets early.
MAX_PACKET_BYTES = 64 * 1024 * 1024


class FileChangedError(OSError):
    """The file changed between reading it and replacing it."""


class MetadataContainer(Protocol):
    """Where an XMP packet lives inside one image format.

    Writes must leave the pixel data byte-for-byte untouched and keep the
    file's modification time.
    """

    def supports(self, path: str) -> bool: ...

    def read_xmp(self, path: str) -> Optional[bytes]: ...

    def write_xmp(self, path: str, packet: bytes) -> None: ...
