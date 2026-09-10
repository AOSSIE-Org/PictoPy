# backend/app/utils/memory_scoring.py

"""Memory scoring utility functions.

Note: in_album scoring is unavailable for videos because video exclusion from albums is intentional.
Albums currently only support images/photos.
"""


def calculate_in_album_score(media_type: str, album_id: str | None) -> float:
    # Videos cannot be added to albums; in_album feature is intentional image-only.
    if media_type == "video" or not album_id:
        return 0.0
    return 1.0
