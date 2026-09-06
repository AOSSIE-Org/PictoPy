"""
Replacing a file in a watched folder without the change reading as a user edit.

Anything that rewrites a file inside a registered folder should go through here
rather than opening the path directly.
"""

import os
import tempfile
from typing import Optional

from app.database.self_writes import db_record_self_write
from app.logging.setup_logging import get_logger

logger = get_logger(__name__)

# The temp file lands in the watched folder too, so the watcher recognises and
# ignores it by name. Mirrored in sync-microservice/app/utils/watcher.py.
SELF_WRITE_TEMP_PREFIX = ".pictopy-write-"


def _discard(temp_path: Optional[str]) -> None:
    """Best-effort cleanup; a leftover temp is noise, not a failure worth raising."""
    if not temp_path:
        return
    try:
        os.unlink(temp_path)
    except OSError:
        logger.warning(f"Could not remove temporary file {temp_path}")


def self_write_util_replace(path: str, data: bytes) -> bool:
    """
    Atomically replace a file's contents and record the write for the watcher.

    Writes to a sibling temp file, records the size and mtime that file already
    has, then renames it into place. The rename carries both across unchanged,
    so the ledger row is in the database before the new bytes are visible at the
    watched path -- which matters, because the watcher can fire the moment they
    are.

    Returns False if the file could not be replaced, leaving the original as is.
    """
    target = os.path.abspath(path)
    directory = os.path.dirname(target)
    temp_path: Optional[str] = None

    try:
        # Same directory, so the rename stays on one filesystem and stays atomic.
        handle_fd, temp_path = tempfile.mkstemp(
            dir=directory, prefix=SELF_WRITE_TEMP_PREFIX, suffix=".tmp"
        )
        with os.fdopen(handle_fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            # Without this the rename can land before the bytes do, which on a
            # crash leaves a photo that is neither the old one nor the new one.
            os.fsync(handle.fileno())

        stats = os.stat(temp_path)
        db_record_self_write(target, stats.st_size, int(stats.st_mtime))

        os.replace(temp_path, target)
        return True
    except OSError as e:
        # A locked or read-only file is ordinary on Windows; the caller retries
        # on a later pass rather than treating it as a failed run.
        logger.error(f"Could not replace {path}: {e}")
        _discard(temp_path)
        return False
