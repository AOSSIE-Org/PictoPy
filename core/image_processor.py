# ...existing code...
from utils.cache import cached, invalidate_cache

# Cache image metadata for 10 minutes (600 seconds)
@cached(key_prefix="image_metadata", ttl=600)
def get_image_metadata(image_path):
    # ...existing code...
    return metadata

@cached(key_prefix="image_thumbnail", ttl=3600)
def generate_thumbnail(image_path, size=(200, 200)):
    # ...existing code...
    return thumbnail_path

def update_image_metadata(image_path, metadata):
    # ...existing code...
    # Invalidate metadata cache after update
    invalidate_cache(f"image_metadata:get_image_metadata:{image_path}")
    return result

# Function to invalidate image caches when an image is modified
def invalidate_image_caches(image_path):
    invalidate_cache(f"image_metadata:get_image_metadata:{image_path}")
    invalidate_cache(f"image_thumbnail:generate_thumbnail:{image_path}")
# ...existing code...
