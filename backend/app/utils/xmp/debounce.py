import threading
from concurrent.futures import Future
from typing import Any, Callable, Optional

from app.logging.setup_logging import get_logger

logger = get_logger(__name__)

# Long enough to fold a burst of clicks (favouriting a dozen photos) into one
# pass, short enough that the files catch up while the user is still there.
EXPORT_DEBOUNCE_SECONDS = 5.0


class ExportDebouncer:
    """Turns bursts of edits into one export pass, started after the last edit.

    `submit` queues the pass (on the shared executor) and returns its Future.
    """

    def __init__(
        self,
        submit: Callable[[], "Future[Any]"],
        delay: float = EXPORT_DEBOUNCE_SECONDS,
    ) -> None:
        self._submit = submit
        self._delay = delay
        self._lock = threading.Lock()
        self._timer: Optional[threading.Timer] = None
        self._queued: Optional["Future[Any]"] = None
        self._closed = False

    def notify(self) -> None:
        """An edit happened; (re)start the countdown."""
        with self._lock:
            if self._closed:
                return
            if self._timer is not None:
                self._timer.cancel()
            self._timer = threading.Timer(self._delay, self._fire)
            self._timer.daemon = True
            self._timer.start()

    def _fire(self) -> None:
        with self._lock:
            self._timer = None
            if self._closed:
                return
            queued = self._queued
            # A pass still waiting its turn will see these edits when it runs.
            if queued is not None and not queued.running() and not queued.done():
                return
            try:
                self._queued = self._submit()
            except Exception as e:
                # The edit already stands; the next pipeline pass catches up.
                logger.error(f"Could not queue metadata export: {e}")

    def close(self) -> None:
        with self._lock:
            self._closed = True
            if self._timer is not None:
                self._timer.cancel()
                self._timer = None
