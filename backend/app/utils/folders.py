import uuid
import os
from app.database.folders import db_insert_folders_batch


def folder_util_add_folder_tree(root_path, parent_folder_id=None, AI_Tagging=False, taggingCompleted=None):
    """
    Recursively collect folder data and insert all folders in a single database transaction.
    All folders are initially inserted with NULL parent_id, which is updated after insertion.
    Returns the root folder's UUID and the folder map (containing folder_id and parent_id).
    """
    folders_data = []
    folder_map = {}  # Maps path to (folder_id, parent_id)

    for dirpath, dirnames, _ in os.walk(root_path, topdown=True):
        dirpath = os.path.abspath(dirpath)
        # Generate a UUID for this folder
        this_folder_id = str(uuid.uuid4())

        # Determine parent ID for the map (not for initial insert)
        if dirpath == root_path:
            parent_id = parent_folder_id
        else:
            parent_path = os.path.dirname(dirpath)
            parent_id = folder_map[parent_path][0] if parent_path in folder_map else None

        # Store both folder_id and parent_id in the map
        folder_map[dirpath] = (this_folder_id, parent_id)

        # Time is in Unix format
        last_modified_time = int(os.path.getmtime(dirpath))

        # Add to batch data - always set parent_id to NULL initially
        folders_data.append(
            (
                this_folder_id,
                dirpath,
                None,  # parent_folder_id is always NULL initially
                last_modified_time,
                AI_Tagging,
                taggingCompleted,
            )
        )

    # Insert all folders in a single database transaction
    db_insert_folders_batch(folders_data)

    return folder_map[root_path][0], folder_map
