import os
import threading
import time
import logging
from typing import List, Tuple, Dict, Optional
from watchfiles import watch, Change
from app.database.folders import (
    db_get_all_folder_details,
    db_delete_folders_batch,
    db_get_direct_child_folders,
)
from app.utils.folders import (
    folder_util_add_multiple_folder_trees,
    folder_util_delete_obsolete_folders,
    folder_util_get_filesystem_direct_child_folders,
)
from app.config.settings import *
from app.logging.setup_logging import get_logger

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("watchfiles").setLevel(logging.WARNING)  # Silence watchfiles logger
logging.getLogger("watchfiles.main").setLevel(
    logging.WARNING
)  # Silence watchfiles.main logger

logger = get_logger(__name__)

FolderIdPath = Tuple[str, str]

# Thread lock for global state synchronization
state_lock = threading.Lock()

watcher_thread: Optional[threading.Thread] = None
stop_event = threading.Event()
watched_folders: List[FolderIdPath] = []
folder_id_map: Dict[str, str] = {}


def watcher_util_get_folder_id_if_watched(file_path: str) -> Optional[str]:
    """
    Check if the given file path is one of our watched folders.

    Args:
        file_path: Path to check

    Returns:
        Folder ID if the path is a watched folder, None otherwise
    """
    normalized_path = os.path.abspath(file_path)

    with state_lock:
        for folder_id, folder_path in watched_folders:
            if os.path.abspath(folder_path) == normalized_path:
                return folder_id

    return None


def watcher_util_handle_file_changes(changes: set) -> None:
    """
    Handle file changes detected by watchfiles.

    Args:
        changes: Set of (change_type, file_path) tuples
    """
    deleted_folder_ids = []

    affected_folders = {}  # folder_path -> folder_id mapping

    for change, file_path in changes:
        if change == Change.deleted:
            deleted_folder_id = watcher_util_get_folder_id_if_watched(file_path)
            if deleted_folder_id:
                deleted_folder_ids.append(deleted_folder_id)
                continue

        closest_folder = watcher_util_find_closest_parent_folder(
            file_path, watched_folders
        )
        if closest_folder:
            folder_id, folder_path = closest_folder
            affected_folders[folder_path] = folder_id

    for folder_path, folder_id in affected_folders.items():
        watcher_util_call_sync_folder_api(folder_id, folder_path)

    if deleted_folder_ids:
        logger.info(f"Processing {len(deleted_folder_ids)} deleted folders")
        watcher_util_call_delete_folders_api(deleted_folder_ids)
        watcher_util_restart_folder_watcher()


def watcher_util_find_closest_parent_folder(
    file_path: str, watched_folders: List[FolderIdPath]
) -> Optional[Tuple[str, str]]:
    """
    Find the closest parent folder for a given file path from the watched folders.

    Args:
        file_path: Path to the file that changed
        watched_folders: List of (folder_id, folder_path) tuples

    Returns:
        Tuple of (folder_id, folder_path) if found, None otherwise
    """
    file_path = os.path.abspath(file_path)

    best_match = None
    longest_match_length = 0

    for folder_id, folder_path in watched_folders:
        folder_path = os.path.abspath(folder_path)

        if file_path.startswith(folder_path):
            if file_path == folder_path or file_path[len(folder_path)] == os.sep:
                if len(folder_path) > longest_match_length:
                    longest_match_length = len(folder_path)
                    best_match = (folder_id, folder_path)

    return best_match


def watcher_util_call_sync_folder_api(folder_id: str, folder_path: str) -> None:
    """
    Sync a folder by calling the sync logic directly.

    Args:
        folder_id: ID of the folder to sync
        folder_path: Path of the folder to sync
    """
    try:
        logger.info(f"Syncing folder {folder_path} (ID: {folder_id})")
        
        # Step 1: Get current state from both sources
        db_child_folders = db_get_direct_child_folders(folder_id)
        filesystem_folders = folder_util_get_filesystem_direct_child_folders(folder_path)

        # Step 2: Compare and identify differences
        filesystem_folder_set = set(filesystem_folders)
        db_folder_paths = {fp for fid, fp in db_child_folders}

        folders_to_delete = db_folder_paths - filesystem_folder_set
        folders_to_add = filesystem_folder_set - db_folder_paths

        # Step 3: Perform synchronization operations
        deleted_count, deleted_folders = folder_util_delete_obsolete_folders(
            db_child_folders, folders_to_delete
        )
        added_count, added_folders_with_ids = folder_util_add_multiple_folder_trees(
            folders_to_add, folder_id
        )

        logger.info(
            f"Successfully synced folder {folder_path} (ID: {folder_id}). "
            f"Added {added_count}, deleted {deleted_count}"
        )
        
        # Note: We skip the post_sync_folder_sequence here as it would create
        # a circular dependency and the watcher is already handling file monitoring
        
    except Exception as e:
        logger.error(f"Unexpected error while syncing folder {folder_path}: {e}")


def watcher_util_call_delete_folders_api(folder_ids: List[str]) -> None:
    """
    Delete folders by calling the database function directly.

    Args:
        folder_ids: List of folder IDs to delete
    """
    try:
        logger.info(f"Deleting folders with IDs: {folder_ids}")
        deleted_count = db_delete_folders_batch(folder_ids)
        logger.info(f"Successfully deleted {deleted_count} folder(s) with IDs: {folder_ids}")
    except Exception as e:
        logger.error(f"Unexpected error while deleting folders {folder_ids}: {e}")


def watcher_util_watcher_worker(folder_paths: List[str]) -> None:
    """
    Worker function that runs the file watcher in a background thread.

    Args:
        folder_paths: List of folder paths to watch
    """
    try:
        logger.info(f"Starting watcher for {len(folder_paths)} folders")

        logger.debug(f"Watching folders: {folder_paths}")
        for changes in watch(
            *folder_paths, stop_event=stop_event, recursive=True, debug=False
        ):
            if stop_event.is_set():
                logger.info("Stop event detected in watcher loop")
                break

            if logger.isEnabledFor(10):  # DEBUG level is 10
                from app.utils.watcher_helpers import format_debug_changes

                logger.debug("Detailed changes:\n %s", format_debug_changes(changes))

            watcher_util_handle_file_changes(changes)
    except Exception as e:
        logger.error(f"Error in watcher worker: {e}")
    finally:
        logger.info("Watcher stopped")


def watcher_util_get_existing_folders(
    folders: List[FolderIdPath],
) -> List[FolderIdPath]:
    """
    Filter folders to only include those that exist in the filesystem.

    Args:
        folders: List of (folder_id, folder_path) tuples

    Returns:
        List of existing folders
    """
    existing_folders = []
    for folder_id, folder_path in folders:
        if os.path.exists(folder_path) and os.path.isdir(folder_path):
            existing_folders.append((folder_id, folder_path))
        else:
            logger.warning(f"Folder does not exist: {folder_path}")
    return existing_folders


def watcher_util_is_watcher_running() -> bool:
    """Check if the watcher thread is running."""
    return watcher_thread is not None and watcher_thread.is_alive()


def watcher_util_start_folder_watcher() -> bool:
    """
    Initialize and start the folder watcher with folders from the database.

    Returns:
        True if watcher started successfully, False otherwise
    """
    global watcher_thread, watched_folders, folder_id_map

    if watcher_util_is_watcher_running():
        logger.info("Watcher is already running.")
        return False

    logger.info("Initializing folder watcher...")
    logger.debug("Debug logging is enabled")

    try:
        all_folder_details = db_get_all_folder_details()
        
        folders = [(folder_id, folder_path) for folder_id, folder_path, *_ in all_folder_details]
        
        if not folders:
            logger.info("No folders found in database")
            return False

        logger.info(f"Found {len(folders)} folders in database")

        existing_folders = watcher_util_get_existing_folders(folders)
        if not existing_folders:
            logger.info("No existing folders to watch")
            return False

        with state_lock:
            watched_folders = existing_folders
            folder_id_map = {
                folder_path: folder_id for folder_id, folder_path in existing_folders
            }

        folder_paths = [folder_path for _, folder_path in existing_folders]

        logger.info(f"Starting to watch {len(folder_paths)} folders:")
        for folder_id, folder_path in existing_folders:
            logger.info(f"  - {folder_path} (ID: {folder_id})")

        stop_event.clear()
        watcher_thread = threading.Thread(
            target=watcher_util_watcher_worker,
            args=(folder_paths,),
            daemon=True,  # Dies when main program exits
        )
        watcher_thread.start()

        logger.info("Folder watcher started successfully")
        return True

    except Exception as e:
        logger.error(f"Error starting folder watcher: {e}")
        return False


def watcher_util_stop_folder_watcher() -> None:
    """Stop the folder watcher."""
    global watcher_thread, watched_folders, folder_id_map

    if not watcher_util_is_watcher_running():
        logger.info("Watcher is not running")
        return

    try:
        logger.info("Stopping folder watcher...")

        stop_event.set()

        watcher_thread.join(timeout=5.0)

        if watcher_thread.is_alive():
            logger.warning("Warning: Watcher thread did not stop gracefully")
        else:
            logger.info("Watcher stopped successfully")

    except Exception as e:
        logger.error(f"Error stopping watcher: {e}")
    finally:
        watcher_thread = None
        with state_lock:
            watched_folders = []
            folder_id_map = {}


def watcher_util_restart_folder_watcher() -> bool:
    """
    Restart the folder watcher by stopping the current one and starting fresh.

    Returns:
        True if restart was successful, False otherwise
    """
    logger.info("Restarting folder watcher...")
    watcher_util_stop_folder_watcher()
    return watcher_util_start_folder_watcher()


def watcher_util_get_watcher_info() -> dict:
    """Get information about the current watcher state."""
    with state_lock:
        watched_folders_copy = [
            {"id": folder_id, "path": folder_path}
            for folder_id, folder_path in watched_folders
        ]
        folders_count = len(watched_folders)
    
    return {
        "is_running": watcher_util_is_watcher_running(),
        "folders_count": folders_count,
        "thread_alive": watcher_thread.is_alive() if watcher_thread else False,
        "thread_id": watcher_thread.ident if watcher_thread else None,
        "watched_folders": watched_folders_copy,
    }


def watcher_util_wait_for_watcher() -> None:
    """
    Wait for the watcher to finish (useful for keeping the program running).
    """
    if watcher_thread and watcher_thread.is_alive():
        try:
            watcher_thread.join()  # Wait indefinitely
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
            watcher_util_stop_folder_watcher()
    else:
        logger.info("No watcher thread to wait for")
