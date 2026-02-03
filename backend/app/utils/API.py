import requests
from app.config.settings import SYNC_MICROSERVICE_URL
import logging

logger = logging.getLogger(__name__)


def API_util_restart_sync_microservice_watcher():
    """
    Send a POST request to restart the sync microservice watcher.

    Returns:
        bool: True if request was successful, False otherwise
    """
    try:
        url = f"{SYNC_MICROSERVICE_URL}/watcher/restart"
        response = requests.post(url, timeout=30)

        if response.status_code == 200:
            logger.info("Successfully restarted sync microservice watcher")
            return True
        else:
            logger.warning(
                f"Failed to restart sync microservice watcher. Status code: {response.status_code}"
            )
            return False

    except requests.exceptions.RequestException as e:
        logger.error(f"Error communicating with sync microservice: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error restarting sync microservice watcher: {e}")
        return False
