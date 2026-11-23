from typing import List, Optional

from .base import MetadataContainer
from .png import PngContainer

# Order matters only if two containers claim the same file; add JPEG etc. here.
_CONTAINERS: List[MetadataContainer] = [PngContainer()]


def get_container(path: str) -> Optional[MetadataContainer]:
    """The container that can carry XMP for this file, sniffed from its bytes."""
    for container in _CONTAINERS:
        if container.supports(path):
            return container
    return None
