"""
Resolving an image request against a share.

The receiver only ever sends IDs. Turning an ID into a path happens here, and
only after the image has been confirmed to belong to the shared album — without
that check a share token would be a read handle over the whole images table.
"""

from __future__ import annotations

import os
from typing import List, Optional

from app.database.albums import (
    db_album_contains_image,
    db_get_album,
    db_get_album_images,
)
from app.database.images import db_get_image_by_id


def share_media_album_name(album_id: str) -> Optional[str]:
    """
    The album's display name, or None if it has been deleted since sharing.

    `is_locked` is deliberately ignored: an album's local lock is a separate
    concern from network sharing, which carries its own authorization.
    """
    album = db_get_album(album_id)
    return album["album_name"] if album else None


def share_media_image_ids(album_id: str) -> List[str]:
    return db_get_album_images(album_id)


def share_media_resolve_path(
    album_id: str, image_id: str, *, thumbnail: bool
) -> Optional[str]:
    """
    The file backing one image of a shared album, or None if it is not part of
    that album, is unknown, or has vanished from disk since indexing.
    """
    if not db_album_contains_image(album_id, image_id):
        return None

    image = db_get_image_by_id(image_id)
    if not image:
        return None

    path = image.get("thumbnailPath") if thumbnail else image.get("path")
    # A thumbnail can be missing for an image indexed before it was generated;
    # the original is a correct, if heavier, substitute.
    if thumbnail and not path:
        path = image.get("path")
    if not path or not os.path.isfile(path):
        return None
    return path
