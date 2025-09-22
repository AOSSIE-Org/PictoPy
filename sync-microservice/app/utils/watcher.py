import os
import threading
import time
from typing import List, Tuple, Dict, Optional
from watchfiles import watch, Change
import httpx
from app.database.folders import db_get_all_folders_with_ids
from app.config.settings import PRIMARY_BACKEND_URL

FolderIdPath = Tuple[str, str]

# Global variables to track watcher state
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
    # Normalize the file path
    normalized_path = os.path.abspath(file_path)

    # Check if this path matches any of our watched folders
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

    for change, file_path in changes:
        print(f"File change detected: {change} - {file_path}")

        # Check if this is a deleted folder that we're watching
        is_deleted_watched_folder = False
        if change == Change.deleted:
            deleted_folder_id = watcher_util_get_folder_id_if_watched(file_path)
            if deleted_folder_id:
                print(
                    f"  Watched folder deleted: {file_path} (ID: {deleted_folder_id})"
                )
                deleted_folder_ids.append(deleted_folder_id)
                is_deleted_watched_folder = True

        # Execute for additions, modifications, and also for deleted image files within watched folders
        # (ensuring image deletions trigger a sync of their parent folders)
        if not is_deleted_watched_folder:
            closest_folder = watcher_util_find_closest_parent_folder(
                file_path, watched_folders
            )

            if closest_folder:
                folder_id, folder_path = closest_folder
                print(f"  Closest parent folder: {folder_path} (ID: {folder_id})")

                watcher_util_call_sync_folder_api(folder_id, folder_path)
            else:
                print(f"  No watched parent folder found for: {file_path}")

    # If any watched folders were deleted, call the delete API
    if deleted_folder_ids:
        print(f"Calling delete API for {len(deleted_folder_ids)} deleted folders")
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
    # Normalize the file path
    file_path = os.path.abspath(file_path)

    best_match = None
    longest_match_length = 0

    for folder_id, folder_path in watched_folders:
        # Normalize the folder path
        folder_path = os.path.abspath(folder_path)

        # Check if this folder is a parent of the file
        if file_path.startswith(folder_path):
            # Ensure it's a proper parent (not just a prefix)
            if file_path == folder_path or file_path[len(folder_path)] == os.sep:
                # Choose the longest matching path (closest parent)
                if len(folder_path) > longest_match_length:
                    longest_match_length = len(folder_path)
                    best_match = (folder_id, folder_path)
    print("best match: ", best_match)

    return best_match


def watcher_util_call_sync_folder_api(folder_id: str, folder_path: str) -> None:
    """
    Call the primary backend's sync-folder API endpoint.

    Args:
        folder_id: ID of the folder to sync
        folder_path: Path of the folder to sync
    """
    try:
        url = f"{PRIMARY_BACKEND_URL}/folders/sync-folder"
        payload = {"folder_path": folder_path, "folder_id": folder_id}

        with httpx.Client(timeout=30.0) as client:
            response = client.request("POST", url, json=payload)

            if response.status_code == 200:
                print(f"Successfully synced folder {folder_path} (ID: {folder_id})")
            else:
                print(
                    f"Failed to sync folder {folder_path}. Status: {response.status_code}, Response: {response.text}"
                )

    except httpx.RequestError as e:
        print(f"Network error while syncing folder {folder_path}: {e}")
    except Exception as e:
        print(f"Unexpected error while syncing folder {folder_path}: {e}")


def watcher_util_call_delete_folders_api(folder_ids: List[str]) -> None:
    """
    Call the primary backend's delete-folders API endpoint.

    Args:
        folder_ids: List of folder IDs to delete
    """
    try:
        url = f"{PRIMARY_BACKEND_URL}/folders/delete-folders"
        payload = {"folder_ids": folder_ids}

        with httpx.Client(timeout=30.0) as client:
            response = client.request("DELETE", url, json=payload)

            if response.status_code == 200:
                print(f"Successfully deleted folders with IDs: {folder_ids}")
            else:
                print(
                    f"Failed to delete folders. Status: {response.status_code}, Response: {response.text}"
                )

    except httpx.RequestError as e:
        print(f"Network error while deleting folders {folder_ids}: {e}")
    except Exception as e:
        print(f"Unexpected error while deleting folders {folder_ids}: {e}")


def watcher_util_watcher_worker(folder_paths: List[str]) -> None:
    """
    Worker function that runs the file watcher in a background thread.

    Args:
        folder_paths: List of folder paths to watch
    """
    try:
        print(f"Starting watcher for {len(folder_paths)} folders")
        for changes in watch(*folder_paths, stop_event=stop_event, recursive=False):
            if stop_event.is_set():
                print("Stop event detected in watcher loop")
                break
            watcher_util_handle_file_changes(changes)
    except Exception as e:
        print(f"Error in watcher worker: {e}")
    finally:
        print("Watcher stopped")


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
            print(f"Warning: Folder does not exist: {folder_path}")
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
        print("Watcher is already running.")
        return False

    print("Initializing folder watcher...")

    try:
        # Simple synchronous database call
        folders = db_get_all_folders_with_ids()
        if not folders:
            print("No folders found in database")
            return False

        print(f"Found {len(folders)} folders in database")

        # Simple synchronous file system checks
        existing_folders = watcher_util_get_existing_folders(folders)
        if not existing_folders:
            print("No existing folders to watch")
            return False

        watched_folders = existing_folders
        folder_id_map = {
            folder_path: folder_id for folder_id, folder_path in existing_folders
        }

        folder_paths = [folder_path for _, folder_path in existing_folders]

        print(f"Starting to watch {len(folder_paths)} folders:")
        for folder_id, folder_path in existing_folders:
            print(f"  - {folder_path} (ID: {folder_id})")

        # Reset stop event and start background thread
        stop_event.clear()
        watcher_thread = threading.Thread(
            target=watcher_util_watcher_worker,
            args=(folder_paths,),
            daemon=True,  # Dies when main program exits
        )
        watcher_thread.start()

        print("Folder watcher started successfully")
        return True

    except Exception as e:
        print(f"Error starting folder watcher: {e}")
        return False


def watcher_util_stop_folder_watcher() -> None:
    """Stop the folder watcher."""
    global watcher_thread, watched_folders, folder_id_map

    if not watcher_util_is_watcher_running():
        print("Watcher is not running")
        return

    try:
        print("Stopping folder watcher...")

        # Signal the watcher to stop
        stop_event.set()

        # Wait for thread to finish
        watcher_thread.join(timeout=5.0)

        if watcher_thread.is_alive():
            print("Warning: Watcher thread did not stop gracefully")
        else:
            print("Watcher stopped successfully")

    except Exception as e:
        print(f"Error stopping watcher: {e}")
    finally:
        watcher_thread = None
        # Clear state
        watched_folders = []
        folder_id_map = {}


def watcher_util_restart_folder_watcher() -> bool:
    """
    Restart the folder watcher by stopping the current one and starting fresh.

    Returns:
        True if restart was successful, False otherwise
    """
    print("Restarting folder watcher...")
    watcher_util_stop_folder_watcher()
    return watcher_util_start_folder_watcher()


def watcher_util_get_watcher_info() -> dict:
    """Get information about the current watcher state."""
    return {
        "is_running": watcher_util_is_watcher_running(),
        "folders_count": len(watched_folders),
        "thread_alive": watcher_thread.is_alive() if watcher_thread else False,
        "thread_id": watcher_thread.ident if watcher_thread else None,
        "watched_folders": [
            {"id": folder_id, "path": folder_path}
            for folder_id, folder_path in watched_folders
        ],
    }


def watcher_util_wait_for_watcher() -> None:
    """
    Wait for the watcher to finish (useful for keeping the program running).
    """
    if watcher_thread and watcher_thread.is_alive():
        try:
            watcher_thread.join()  # Wait indefinitely
        except KeyboardInterrupt:
            print("Interrupted by user")
            watcher_util_stop_folder_watcher()
    else:
        print("No watcher thread to wait for")


# Simple usage examples
def main():
    """Simple example of how to use the folder watcher."""
    print("Starting folder watcher example...")

    success = watcher_util_start_folder_watcher()
    if success:
        print("Watcher started, will run for 10 seconds...")
        try:
            time.sleep(10)  # Just sleep - no async complexity!
        except KeyboardInterrupt:
            print("Interrupted by user")
        finally:
            watcher_util_stop_folder_watcher()
    else:
        print("Failed to start watcher")

    print("Example finished")
