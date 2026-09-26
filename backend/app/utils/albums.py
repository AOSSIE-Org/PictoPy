"""Album workflows that reach across more than one table."""

import sqlite3
import uuid
from typing import TypedDict

from app.database.albums import db_create_album_with_images, db_get_album_by_name
from app.database.memories import db_get_memory, db_get_memory_images


class AlbumFromMemoryResult(TypedDict):
    album_id: str
    image_count: int


class AlbumFromMemoryError(Exception):
    """Base for the ways a conversion can legitimately fail."""


class MemoryNotFoundError(AlbumFromMemoryError):
    pass


class MemoryHasNoPhotosError(AlbumFromMemoryError):
    pass


class AlbumNameTakenError(AlbumFromMemoryError):
    pass


def album_util_create_from_memory(memory_id: str, name: str) -> AlbumFromMemoryResult:
    """
    Copy a memory's photos into a new album.

    The memory itself is left untouched, so the same one can be converted
    again under a different name. Any clips are left behind: album_images
    references images, and albums have no video support.

    Raises AlbumFromMemoryError subclasses for the expected failures, so the
    caller decides how to report them.
    """
    memory = db_get_memory(memory_id)
    if not memory:
        raise MemoryNotFoundError(memory_id)

    image_ids = [image["id"] for image in db_get_memory_images(memory_id)]
    if not image_ids:
        raise MemoryHasNoPhotosError(memory_id)

    if db_get_album_by_name(name):
        raise AlbumNameTakenError(name)

    album_id = str(uuid.uuid4())
    try:
        image_count = db_create_album_with_images(
            album_id, name, memory.get("subtitle") or "", image_ids
        )
    except sqlite3.IntegrityError as e:
        # The name check above is not atomic. Re-check rather than assume a
        # conflict: the same error covers an image that vanished mid-request.
        if db_get_album_by_name(name):
            raise AlbumNameTakenError(name) from e
        raise

    return AlbumFromMemoryResult(album_id=album_id, image_count=image_count)
