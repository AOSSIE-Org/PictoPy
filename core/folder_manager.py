# ...existing code...
from utils.cache import cached, invalidate_cache

# Cache folder structure for 5 minutes (300 seconds)
@cached(key_prefix="folder_structure", ttl=300)
def get_folder_structure(root_path=None):
    # ...existing code...
    return folder_structure

@cached(key_prefix="folder_contents", ttl=300)
def get_folder_contents(folder_path):
    # ...existing code...
    return contents

def create_folder(parent_path, folder_name):
    # ...existing code...
    # Invalidate folder caches after creating a new folder
    invalidate_cache("folder_structure:get_folder_structure")
    invalidate_cache(f"folder_contents:get_folder_contents:{parent_path}")
    return result

def rename_folder(folder_path, new_name):
    # ...existing code...
    # Invalidate folder caches after renaming
    invalidate_cache("folder_structure:get_folder_structure")
    parent_path = os.path.dirname(folder_path)
    invalidate_cache(f"folder_contents:get_folder_contents:{parent_path}")
    return result

def delete_folder(folder_path):
    # ...existing code...
    # Invalidate folder caches after deletion
    invalidate_cache("folder_structure:get_folder_structure")
    parent_path = os.path.dirname(folder_path)
    invalidate_cache(f"folder_contents:get_folder_contents:{parent_path}")
    return result
# ...existing code...
