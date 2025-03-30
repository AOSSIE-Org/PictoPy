# ...existing code...
from utils.cache import cached, invalidate_cache

# Cache albums for 1 hour (3600 seconds)
@cached(key_prefix="albums", ttl=3600)
def get_all_albums():
    # ...existing code...
    return albums


@cached(key_prefix="album", ttl=3600)
def get_album(album_id):
    # ...existing code...
    return album


def add_album(album_data):
    # ...existing code...
    # Invalidate albums cache after adding a new album
    invalidate_cache("albums:get_all_albums")
    return result


def update_album(album_id, album_data):
    # ...existing code...
    # Invalidate specific album cache and albums list
    invalidate_cache(f"album:get_album:{album_id}")
    invalidate_cache("albums:get_all_albums")
    return result


def delete_album(album_id):
    # ...existing code...
    # Invalidate caches after deletion
    invalidate_cache(f"album:get_album:{album_id}")
    invalidate_cache("albums:get_all_albums")
    return result


# ...existing code...
