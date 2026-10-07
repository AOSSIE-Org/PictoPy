from typing import Optional, Protocol


class MetadataContainer(Protocol):
    """Where an XMP packet lives inside one image format.

    Implementations must leave the pixel data byte-for-byte untouched.
    """

    def supports(self, path: str) -> bool: ...

    def read_xmp(self, path: str) -> Optional[bytes]: ...

    def write_xmp(self, path: str, packet: bytes) -> None: ...
