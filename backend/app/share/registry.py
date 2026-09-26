"""
Active shares, held in memory only.

Deliberately not a database table: shares are meant to die with the process, and
keeping them here makes that structural rather than something a cleanup job has
to enforce. It also means no share token is ever written to disk.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

import bcrypt

# Long enough that guessing is hopeless; the token is the only credential
# protecting an album on a network anyone else may also be on.
_TOKEN_BYTES = 32

# bcrypt silently truncates past 72 bytes, so anything longer would be accepted
# at creation and then not be the password the user thinks it is.
PASSWORD_MAX_BYTES = 72

# A wrong password costs a bcrypt verification, which already caps guessing at a
# few tries a second. The cooldown is what stops an overnight script.
_MAX_FAILED_UNLOCKS = 10
_UNLOCK_COOLDOWN = timedelta(seconds=30)

# Signs the unlock cookie. Regenerated per process, so every unlock dies with
# PictoPy exactly as the shares themselves do.
_unlock_secret = secrets.token_bytes(32)


@dataclass
class ShareEntry:
    """One album being served, for as long as this process lives."""

    token: str
    album_id: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    password_hash: Optional[bytes] = None
    failed_unlocks: int = 0
    # Attempts admitted but still being hashed; counted so concurrent requests
    # cannot collectively overshoot the limit.
    pending_unlocks: int = 0
    locked_until: Optional[datetime] = None

    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return _now() >= self.expires_at

    @property
    def is_protected(self) -> bool:
        return self.password_hash is not None


_shares: Dict[str, ShareEntry] = {}
# Uvicorn runs sync route handlers in a threadpool, so the dict is reachable
# from more than one thread.
_lock = threading.Lock()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def share_registry_create(
    album_id: str,
    expires_in_minutes: Optional[int] = None,
    password: Optional[str] = None,
) -> ShareEntry:
    """Issue a token for an album. Any previous share of it stays valid."""
    expires_at = (
        _now() + timedelta(minutes=expires_in_minutes)
        if expires_in_minutes is not None
        else None
    )
    password_hash = (
        bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()) if password else None
    )
    entry = ShareEntry(
        token=secrets.token_urlsafe(_TOKEN_BYTES),
        album_id=album_id,
        created_at=_now(),
        expires_at=expires_at,
        password_hash=password_hash,
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


def share_registry_is_throttled(entry: ShareEntry) -> bool:
    """
    Whether unlock attempts are in cooldown.

    Only for wording the message shown to the visitor; the refusal itself is
    enforced inside share_registry_unlock.
    """
    with _lock:
        return entry.locked_until is not None and _now() < entry.locked_until


def share_registry_unlock(entry: ShareEntry, password: str) -> Optional[str]:
    """
    Check a password and, on success, mint the value for the unlock cookie.

    None means the visitor stays locked out, whether the password was wrong, was
    longer than one could ever have been set, or too many attempts have already
    been made.
    """
    if entry.password_hash is None:
        return None

    candidate = password.encode("utf-8")
    # Creating a share refuses anything longer, so this cannot be the password.
    # Checking before hashing also keeps oversized form input away from bcrypt,
    # which truncates at this limit here and rejects it outright in 4.x.
    if len(candidate) > PASSWORD_MAX_BYTES:
        return None

    if not _reserve_attempt(entry):
        return None

    accepted = False
    try:
        # Deliberately outside the lock: bcrypt takes a few hundred milliseconds
        # and holding the registry that long would serialise every request.
        accepted = bcrypt.checkpw(candidate, entry.password_hash)
    finally:
        _release_attempt(entry, accepted)

    if not accepted:
        return None
    return _unlock_signature(entry.token, entry.password_hash)


def _reserve_attempt(entry: ShareEntry) -> bool:
    """
    Claim one of the share's unlock attempts, or refuse.

    Admission is decided before the password is checked rather than after. Sync
    handlers run in uvicorn's threadpool, so a burst of requests would otherwise
    all read the same attempt count and hash concurrently, and the limit would
    only bound how many rounds an attacker needs rather than how many guesses.
    """
    with _lock:
        if entry.locked_until is not None:
            if _now() < entry.locked_until:
                return False
            entry.locked_until = None
            entry.failed_unlocks = 0
        if entry.pending_unlocks + entry.failed_unlocks >= _MAX_FAILED_UNLOCKS:
            return False
        entry.pending_unlocks += 1
        return True


def _release_attempt(entry: ShareEntry, accepted: bool) -> None:
    """
    Record how a claimed attempt turned out.

    Only failures count towards the cooldown, so a share stays open however many
    people unlock it correctly.
    """
    with _lock:
        entry.pending_unlocks -= 1
        if accepted:
            entry.failed_unlocks = 0
            return
        entry.failed_unlocks += 1
        if entry.failed_unlocks >= _MAX_FAILED_UNLOCKS:
            entry.locked_until = _now() + _UNLOCK_COOLDOWN


def share_registry_is_unlocked(entry: ShareEntry, cookie: Optional[str]) -> bool:
    """
    Whether a visitor holding this cookie may see the album.

    The cookie is a signature rather than a stored session id, so nothing here
    grows with the number of devices that open a share.
    """
    if entry.password_hash is None:
        return True
    if not cookie:
        return False
    return hmac.compare_digest(
        cookie, _unlock_signature(entry.token, entry.password_hash)
    )


def _unlock_signature(token: str, password_hash: bytes) -> str:
    """
    The cookie value proving one password check succeeded.

    Bound to both the share token and its hash, so a cookie cannot be replayed
    against another share and stops working if the password is ever changed.
    """
    message = token.encode("utf-8") + b":" + password_hash
    return hmac.new(_unlock_secret, message, hashlib.sha256).hexdigest()


def share_registry_clear() -> None:
    with _lock:
        _shares.clear()
