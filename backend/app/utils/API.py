import logging

logger = logging.getLogger(__name__)

def API_util_restart_sync_microservice_watcher():
    """
    Restart the folder watcher (now integrated into the backend).

    Returns:
        bool: True if restart was successful, False otherwise
    """
    try:
        from app.utils.watcher import watcher_util_restart_folder_watcher
        success = watcher_util_restart_folder_watcher()
        if success:
            logger.info("Successfully restarted folder watcher")
            return True
        else:
            logger.warning("Failed to restart folder watcher")
            return False
    except Exception as e:
        logger.error(f"Unexpected error restarting folder watcher: {e}")
        return False
