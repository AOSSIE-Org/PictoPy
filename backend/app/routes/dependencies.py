"""Dependencies shared by the route modules."""

from fastapi import Request
from starlette.datastructures import State

from app.logging.setup_logging import get_logger

logger = get_logger(__name__)


def get_state(request: Request) -> State:
    """Application state, which is where the shared executors live."""
    return request.app.state


def request_metadata_export(app_state: State) -> None:
    """Note an edit that changes exported metadata; a debounced pass follows.

    Never raises: the edit already stands whether or not export can be queued,
    and the pass itself does nothing while the Settings toggle is off.
    """
    try:
        debouncer = getattr(app_state, "metadata_export_debouncer", None)
        if debouncer is not None:
            debouncer.notify()
    except Exception as e:
        logger.error(f"Could not schedule metadata export: {e}")
