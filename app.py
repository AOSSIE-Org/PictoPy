# ...existing code...
from utils.cache import invalidate_cache


# Add cache reset option when application starts
def initialize_app():
    # ...existing code...
    # Clear any stale cache data on startup
    invalidate_cache()
    # ...existing code...


# If there's a refresh functionality, update it to clear relevant caches
def refresh_data():
    # ...existing code...
    # Clear specific caches that need refreshing
    invalidate_cache("albums:get_all_albums")
    invalidate_cache("folder_structure:get_folder_structure")
    # ...existing code...


# ...existing code...
