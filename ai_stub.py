from typing import Dict, List
from models import SmartAlbum, Photo


def _match_tag_against_name(tag: str, name: str) -> bool:
    """Simple matching: lowercase, check substring match to be robust to plurals.
    
    WARNING: This is a naive stub that will produce false positives
    (e.g., 'cat' matches 'concatenate'). Replace with word-boundary 
    matching or ML-based tagging for production use.
    """
    return name.lower() in tag.lower() or tag.lower() in name.lower()


def refresh_album_contents(album: SmartAlbum, photos: Dict[str, Photo]) -> List[str]:
    """Return a list of photo ids appropriate for the album based on its type.

    - For `object` albums we treat the album `name` as the target tag (e.g., "Cats").
    - For `face` albums we return photos that have faces > 0.
    - For `manual` or unknown types we return the existing `album.photos`.

    This is a lightweight stub you can replace with real image recognition later.
    """
    if album.type == "object":
        target = album.name.strip().lower()
        matched = []
        for pid, p in photos.items():
            for t in p.tags:
                if _match_tag_against_name(t, target):
                    matched.append(pid)
                    break
        return matched

    if album.type == "face":
        return [pid for pid, p in photos.items() if getattr(p, "faces", 0) > 0]

    return album.photos
