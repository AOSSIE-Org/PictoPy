"""
Active shares, held in memory only.

Deliberately not a database table: shares are meant to die with the process, and
keeping them here makes that structural rather than something a cleanup job has
to enforce. It also means no share token is ever written to disk.
"""

from __future__ import annotations

import secrets
import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

# Long enough that guessing is hopeless; the token is the only credential
# protecting an album on a network anyone else may also be on.
_TOKEN_BYTES = 32


@dataclass
class ShareEntry:
    """One album being served, for as long as this process lives."""

    token: str
    album_id: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    unlock_tokens: set = field(default_factory=set)

    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return _now() >= self.expires_at


_shares: Dict[str, ShareEntry] = {}
# Uvicorn runs sync route handlers in a threadpool, so the dict is reachable
# from more than one thread.
_lock = threading.Lock()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def share_registry_create(
    album_id: str, expires_in_minutes: Optional[int] = None
) -> ShareEntry:
    """Issue a token for an album. Any previous share of it stays valid."""
    expires_at = (
        _now() + timedelta(minutes=expires_in_minutes)
        if expires_in_minutes is not None
        else None
    )
    entry = ShareEntry(
        token=secrets.token_urlsafe(_TOKEN_BYTES),
        album_id=album_id,
        created_at=_now(),
        expires_at=expires_at,
    )
    with _lock:
        _shares[entry.token] = entry
    return entry


def share_registry_get(token: str) -> Optional[ShareEntry]:
    """
    The live share for a token, or None.

    An expired entry is dropped here rather than swept on a timer, so expiry
    needs no background task.
    """
    with _lock:
        entry = _shares.get(token)
        if entry is None:
            return None
        if entry.is_expired:
            del _shares[token]
            return None
        return entry


def share_registry_list() -> List[ShareEntry]:
    """Every share that is still live, newest first."""
    with _lock:
        live = [entry for entry in _shares.values() if not entry.is_expired]
    return sorted(live, key=lambda entry: entry.created_at, reverse=True)


def share_registry_revoke(token: str) -> bool:
    """True if a share was removed, False if the token was already gone."""
    with _lock:
        return _shares.pop(token, None) is not None


def share_registry_count() -> int:
    """Live share count; the server stops once this reaches zero."""
    with _lock:
        return sum(1 for entry in _shares.values() if not entry.is_expired)


def share_registry_clear() -> None:
    with _lock:
        _shares.clear()
