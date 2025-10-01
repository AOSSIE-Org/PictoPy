import uuid
import os
from typing import List, Tuple

from fastapi import HTTPException, status
from app.database.folders import (
    db_update_parent_ids_for_subtree,
    db_delete_folders_batch,
)
from app.schemas.folders import ErrorResponse
from app.logging.setup_logging import get_logger

logger = get_logger(__name__)


def folder_util_add_folder_tree(
    root_path, parent_folder_id=None, AI_Tagging=False, taggingCompleted=None
):
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
            parent_id = (
                folder_map[parent_path][0] if parent_path in folder_map else None
            )

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


def folder_util_get_filesystem_direct_child_folders(folder_path: str) -> List[str]:
    """
    Get all direct child directories from the filesystem.

    Args:
        folder_path: Path to the parent folder

    Returns:
        List of absolute paths to direct child directories

    Raises:
        HTTPException: If permission denied or other filesystem errors
    """
    try:
        filesystem_folders = []
        for item in os.listdir(folder_path):
            item_path = os.path.join(folder_path, item)
            if os.path.isdir(item_path):
                filesystem_folders.append(os.path.abspath(item_path))
        return filesystem_folders
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorResponse(
                success=False,
                error="Permission denied",
                message=f"No permission to read folder '{folder_path}'",
            ).model_dump(),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                error="Filesystem error",
                message=f"Error reading folder '{folder_path}': {str(e)}",
            ).model_dump(),
        )


def folder_util_delete_obsolete_folders(
    db_child_folders: List[Tuple[str, str]], folders_to_delete: set
) -> Tuple[int, List[str]]:
    """
    Delete folders from the database that are no longer present in the filesystem.

    Args:
        db_child_folders: List of (folder_id, folder_path) tuples from database
        folders_to_delete: Set of folder paths to delete

    Returns:
        Tuple of (deleted_count, deleted_folders_list)
    """
    if not folders_to_delete:
        return 0, []

    # Get the folder IDs for the folders to delete
    folder_ids_to_delete = [
        folder_id
        for folder_id, folder_path in db_child_folders
        if folder_path in folders_to_delete
    ]

    if folder_ids_to_delete:
        deleted_count = db_delete_folders_batch(folder_ids_to_delete)
        return deleted_count, list(folders_to_delete)

    return 0, []


def folder_util_add_multiple_folder_trees(
    folders_to_add: set, parent_folder_id: str
) -> Tuple[int, List[Tuple[str, str]]]:
    """
    Add multiple folder trees with same parent to the database.

    Args:
        folders_to_add: Set of folder paths to add
        parent_folder_id: ID of the parent folder

    Returns:
        Tuple of (added_count, added_folders_list) where added_folders_list contains (folder_id, folder_path) tuples
    """
    if not folders_to_add:
        return 0, []

    added_folders = []  # List of (folder_id, folder_path) tuples
    added_count = 0

    for folder_path in folders_to_add:
        try:
            # Add each new folder tree (including its subdirectories)
            root_folder_id, folder_map = folder_util_add_folder_tree(
                root_path=folder_path,
                parent_folder_id=parent_folder_id,
                AI_Tagging=False,  # Default to False for new folders
                taggingCompleted=False,
            )

            # Update parent IDs for the new folder tree
            db_update_parent_ids_for_subtree(folder_path, folder_map)

            # Add all folders from the folder_map as (folder_id, folder_path) tuples
            for folder_path_in_map, (folder_id_in_map, _) in folder_map.items():
                added_folders.append((folder_id_in_map, folder_path_in_map))

            added_count += len(folder_map)  # Count all folders in the tree

        except Exception as e:
            # Log the error but continue with other folders
            logger.error(f"Error adding folder {folder_path}: {e}")

    return added_count, added_folders
