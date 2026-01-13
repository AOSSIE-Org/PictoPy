import os
import threading
import time
import logging
import queue
from typing import List, Tuple, Dict, Optional, Set
from watchfiles import watch, Change
import httpx
from app.database.folders import db_get_all_folders_with_ids
from app.config.settings import PRIMARY_BACKEND_URL
from app.logging.setup_logging import get_sync_logger

# Configure third-party loggers
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("watchfiles").setLevel(logging.WARNING)

logger = get_sync_logger(__name__)

FolderIdPath = Tuple[str, str]

# Configuration constants
MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 2  # seconds
MAX_BACKOFF = 60  # seconds
QUEUE_MAX_SIZE = 1000
DEAD_LETTER_MAX_SIZE = 100
MAX_WATCHER_FAILURES = 5
WATCHER_RESTART_DELAY = 5  # seconds

# Global variables
watcher_thread: Optional[threading.Thread] = None
processor_thread: Optional[threading.Thread] = None
stop_event = threading.Event()
watcher_died_event = threading.Event()

# Initialize queues at module level so they persist across restarts
event_queue: queue.Queue = queue.Queue(maxsize=QUEUE_MAX_SIZE)
dead_letter_queue: queue.Queue = queue.Queue(maxsize=DEAD_LETTER_MAX_SIZE)

watched_folders: List[FolderIdPath] = []
folder_id_map: Dict[str, str] = {}
folders_lock = threading.RLock()

# Shared HTTP Client for connection pooling (Keep-Alive)
http_client = httpx.Client(timeout=30.0)


def watcher_util_get_folder_id_if_watched(file_path: str) -> Optional[str]:
    """Check if the given file path is one of our watched folders."""
    # Normalize path and handle Windows case-insensitivity
    normalized_path = os.path.normpath(os.path.abspath(file_path))
    if os.name == 'nt':
        normalized_path = normalized_path.lower()

    with folders_lock:
        for folder_id, folder_path in watched_folders:
            check_path = os.path.normpath(os.path.abspath(folder_path))
            if os.name == 'nt':
                check_path = check_path.lower()
                
            if check_path == normalized_path:
                return folder_id

    return None


def watcher_util_find_closest_parent_folder(
    file_path: str, folders: List[FolderIdPath]
) -> Optional[Tuple[str, str]]:
    """Find the closest parent folder for a given file path from the watched folders."""
    file_path = os.path.abspath(file_path)
    
    # Platform-specific normalization for comparison logic
    compare_file_path = file_path
    if os.name == 'nt':
        compare_file_path = file_path.lower()

    best_match = None
    longest_match_length = 0

    for folder_id, folder_path in folders:
        folder_path = os.path.abspath(folder_path)
        
        # Normalize the folder path for comparison
        compare_folder_path = folder_path
        if os.name == 'nt':
            compare_folder_path = folder_path.lower()

        # Check if file starts with folder path
        if compare_file_path.startswith(compare_folder_path):
            rest = compare_file_path[len(compare_folder_path):]
            if not rest or rest.startswith(os.sep):
                if len(compare_folder_path) > longest_match_length:
                    longest_match_length = len(compare_folder_path)
                    # Return original mixed-case paths, not the lowercased ones
                    best_match = (folder_id, folder_path)

    return best_match


def watcher_util_call_sync_folder_api(folder_id: str, folder_path: str) -> None:
    """Call the primary backend's sync-folder API endpoint using shared client."""
    url = f"{PRIMARY_BACKEND_URL}/folders/sync-folder"
    payload = {"folder_path": folder_path, "folder_id": folder_id}

    try:
        response = http_client.post(url, json=payload)

        if response.status_code == 200:
            logger.info(f"Successfully synced folder {folder_path} (ID: {folder_id})")
        elif response.status_code == 404:
            # If folder is 404 on backend, don't retry, just log warning
            logger.warning(f"Backend reported folder {folder_id} not found during sync.")
        else:
            response.raise_for_status()

    except Exception as e:
        logger.error(f"Error syncing folder {folder_path}: {e}")
        raise


def watcher_util_call_delete_folders_api(folder_ids: List[str]) -> None:
    """Call the primary backend's delete-folders API endpoint using shared client."""
    url = f"{PRIMARY_BACKEND_URL}/folders/delete-folders"
    payload = {"folder_ids": folder_ids}

    try:
        response = http_client.request("DELETE", url, json=payload)

        if response.status_code == 200:
            logger.info(f"Successfully deleted folders with IDs: {folder_ids}")
        elif response.status_code == 404:
            # Idempotency: 404 means already deleted
            logger.info(f"Folders {folder_ids} already deleted or not found.")
        else:
            response.raise_for_status()

    except Exception as e:
        logger.error(f"Error deleting folders {folder_ids}: {e}")
        raise


def watcher_util_handle_file_changes(changes: Set) -> None:
    """Handle file changes detected by watchfiles."""
    deleted_folder_ids = []
    affected_folders = {}

    with folders_lock:
        current_watched_folders = list(watched_folders)

    for change, file_path in changes:
        if change == Change.deleted:
            deleted_folder_id = watcher_util_get_folder_id_if_watched(file_path)
            if deleted_folder_id:
                deleted_folder_ids.append(deleted_folder_id)
                continue

        closest_folder = watcher_util_find_closest_parent_folder(
            file_path, current_watched_folders
        )
        if closest_folder:
            folder_id, folder_path = closest_folder
            affected_folders[folder_path] = folder_id

    # 1. Sync modifications
    for folder_path, folder_id in affected_folders.items():
        watcher_util_call_sync_folder_api(folder_id, folder_path)

    # 2. Handle deletions
    if deleted_folder_ids:
        logger.info(f"Processing {len(deleted_folder_ids)} deleted folders")
        watcher_util_call_delete_folders_api(deleted_folder_ids)
        
        # Schedule restart in separate thread
        # We name it so we can identify it in debug logs
        threading.Thread(
            target=watcher_util_restart_folder_watcher,
            daemon=True,
            name="WatcherRestarter"
        ).start()


def watcher_util_add_to_dead_letter(changes: Set, retry_count: int, error_msg: str) -> None:
    """Add failed event to dead letter queue."""
    try:
        dead_letter_queue.put_nowait({
            "changes": changes,
            "retry_count": retry_count,
            "failed_at": time.time(),
            "error": str(error_msg)
        })
        logger.error(f"Event moved to dead letter queue after {retry_count} retries. Error: {error_msg}")
    except queue.Full:
        logger.critical("Dead letter queue full! Dropping event permanently")


def watcher_util_schedule_retry(changes: Set, retry_count: int) -> None:
    """Schedule a retry for failed event."""
    def do_retry():
        # Don't retry if the app is shutting down
        if stop_event.is_set():
            return
            
        try:
            event_queue.put((changes, retry_count), timeout=5.0)
            logger.debug(f"Requeued event for retry {retry_count}/{MAX_RETRIES}")
        except queue.Full:
            watcher_util_add_to_dead_letter(changes, retry_count, "Queue full during retry")

    backoff = min(RETRY_BACKOFF_BASE ** (retry_count - 1), MAX_BACKOFF)
    timer = threading.Timer(backoff, do_retry)
    timer.daemon = True
    timer.start()


def watcher_util_processor_worker() -> None:
    """Consumer thread: Processes events from the queue."""
    logger.info("Processor worker started")

    while not stop_event.is_set():
        try:
            # Timeout allows periodic check of stop_event
            try:
                item = event_queue.get(timeout=1.0)
            except queue.Empty:
                continue

            changes, retry_count = item if isinstance(item, tuple) else (item, 0)

            try:
                watcher_util_handle_file_changes(changes)
            except Exception as e:
                logger.error(f"Error processing changes (attempt {retry_count + 1}): {e}")

                if retry_count < MAX_RETRIES:
                    watcher_util_schedule_retry(changes, retry_count + 1)
                else:
                    watcher_util_add_to_dead_letter(changes, retry_count, str(e))

            finally:
                event_queue.task_done()

        except Exception as e:
            logger.error(f"Unexpected error in processor worker: {e}")

    logger.info("Processor worker stopped")


def watcher_util_watcher_worker(folder_paths: List[str]) -> None:
    """Producer thread: Watches filesystem and pushes to queue."""
    consecutive_failures = 0

    while not stop_event.is_set() and consecutive_failures < MAX_WATCHER_FAILURES:
        try:
            logger.info(f"Starting watcher for {len(folder_paths)} paths")
            
            # watch() is a blocking generator
            for changes in watch(*folder_paths, stop_event=stop_event, recursive=True):
                if stop_event.is_set():
                    break

                # Backpressure logic: Wait for queue space instead of dropping
                put_successful = False
                while not put_successful and not stop_event.is_set():
                    try:
                        event_queue.put((changes, 0), timeout=1.0)
                        put_successful = True
                    except queue.Full:
                        logger.warning("Event queue full. Watcher paused waiting for processor...")

                # Reset failures on successful iteration
                consecutive_failures = 0

        except Exception as e:
            consecutive_failures += 1
            backoff = min(WATCHER_RESTART_DELAY * (2 ** (consecutive_failures - 1)), MAX_BACKOFF)

            logger.error(
                f"Watcher error ({consecutive_failures}/{MAX_WATCHER_FAILURES}): {e}. "
                f"Restarting in {backoff}s..."
            )

            # CRITICAL FIX: Use wait() instead of sleep()
            # This allows the thread to wake up immediately if stop_event is set
            if stop_event.wait(timeout=backoff):
                break

    if consecutive_failures >= MAX_WATCHER_FAILURES:
        logger.critical("Watcher failed permanently.")
        watcher_died_event.set()

    logger.info("Watcher worker stopped")


def watcher_util_get_existing_folders(
    folders: List[FolderIdPath],
) -> List[FolderIdPath]:
    """Filter folders to only include those that exist in the filesystem."""
    existing_folders = []
    for folder_id, folder_path in folders:
        if os.path.exists(folder_path) and os.path.isdir(folder_path):
            existing_folders.append((folder_id, folder_path))
        else:
            logger.warning(f"Folder does not exist, skipping: {folder_path}")
    return existing_folders


def watcher_util_is_watcher_running() -> bool:
    """Check if the watcher thread is running."""
    return watcher_thread is not None and watcher_thread.is_alive()


def watcher_util_start_folder_watcher() -> bool:
    """Initialize and start the folder watcher."""
    global watcher_thread, processor_thread, watched_folders, folder_id_map
    
    # We do NOT re-initialize event_queue here to prevent data loss on restart

    if watcher_util_is_watcher_running():
        logger.info("Watcher is already running.")
        return False

    logger.info("Initializing folder watcher...")

    try:
        folders = db_get_all_folders_with_ids()
        if not folders:
            logger.info("No folders found in database")
            return False

        existing_folders = watcher_util_get_existing_folders(folders)
        if not existing_folders:
            logger.info("No existing folders to watch")
            return False

        with folders_lock:
            watched_folders = existing_folders
            folder_id_map = {
                folder_path: folder_id for folder_id, folder_path in existing_folders
            }

        folder_paths = [folder_path for _, folder_path in existing_folders]

        # Reset signals
        stop_event.clear()
        watcher_died_event.clear()

        # Start processor (Consumer)
        processor_thread = threading.Thread(
            target=watcher_util_processor_worker,
            daemon=True,
            name="ProcessorWorker"
        )
        processor_thread.start()

        # Start watcher (Producer)
        watcher_thread = threading.Thread(
            target=watcher_util_watcher_worker,
            args=(folder_paths,),
            daemon=True,
            name="WatcherWorker"
        )
        watcher_thread.start()

        logger.info("Folder watcher started successfully")
        return True

    except Exception as e:
        logger.error(f"Error starting folder watcher: {e}")
        return False


def watcher_util_stop_folder_watcher() -> None:
    """Stop the folder watcher and processor."""
    global watcher_thread, processor_thread

    if not watcher_util_is_watcher_running() and (not processor_thread or not processor_thread.is_alive()):
        logger.info("Watcher is not running")
        return

    logger.info("Stopping folder watcher...")
    
    # Signal threads to stop
    stop_event.set()

    current_thread = threading.current_thread()

    # Wait for watcher thread
    if watcher_thread and watcher_thread.is_alive() and current_thread != watcher_thread:
        watcher_thread.join(timeout=5.0)
        if watcher_thread.is_alive():
            logger.warning("Watcher thread did not stop gracefully")

    # Wait for processor thread
    if processor_thread and processor_thread.is_alive() and current_thread != processor_thread:
        processor_thread.join(timeout=10.0)
        if processor_thread.is_alive():
            logger.warning("Processor thread did not stop gracefully")

    logger.info("Watcher stopped successfully")


def watcher_util_restart_folder_watcher() -> bool:
    """Restart the folder watcher by stopping the current one and starting fresh."""
    logger.info("Restarting folder watcher...")
    watcher_util_stop_folder_watcher()
    # Tiny pause to ensure OS releases file handles if necessary
    time.sleep(0.5)
    return watcher_util_start_folder_watcher()


def watcher_util_health_check() -> Tuple[bool, str]:
    """Perform a health check on the watcher service."""
    if watcher_died_event.is_set():
        return False, "Watcher has failed permanently and requires manual restart"

    if not watcher_util_is_watcher_running():
        return True, "Watcher is not running (Stopped state)"

    if not (processor_thread and processor_thread.is_alive()):
        return False, "Processor thread died unexpectedly"

    if event_queue.qsize() > QUEUE_MAX_SIZE * 0.9:
        return False, "Event queue is nearly full - processing may be stuck"

    return True, "Watcher is healthy"