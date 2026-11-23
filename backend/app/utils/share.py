"""
Orchestration for network album shares.

Sits between the HTTP routes and the two pieces of state a share touches: the
in-memory registry and the network listener. Both operations below have to move
those together, which is why they are here rather than in the route module.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import List, Optional, Set, TypedDict

from app.database.albums import db_count_album_images, db_get_album
from app.share.registry import (
    ShareEntry,
    share_registry_count,
    share_registry_create,
    share_registry_purge_expired,
    share_registry_revoke,
)
from app.share.server import share_server_start, share_server_stop
from app.utils.network import network_util_list_candidates


class ShareUrlRecord(TypedDict):
    """One reachable address for a share, as the desktop UI receives it."""

    interface: str
    ip: str
    url: str


class ShareDescription(TypedDict):
    """Everything the desktop UI needs to present one share."""

    token: str
    album_id: str
    album_name: str
    image_count: int
    port: int
    created_at: str
    expires_at: Optional[str]
    is_protected: bool
    urls: List[ShareUrlRecord]


# Creating and revoking both decide whether the listener should be running, and
# they must not interleave: a revoke that finds the registry empty could
# otherwise close the port a concurrent create has just handed out.
_orchestration_lock = asyncio.Lock()


# Strong references: the loop only keeps weak ones, so an unreferenced timer
# could be collected before it fires.
_expiry_timers: Set["asyncio.Task[None]"] = set()


async def share_util_sweep() -> None:
    """Drop expired shares and stop the listener if none are left."""
    async with _orchestration_lock:
        share_registry_purge_expired()
        if share_registry_count() == 0:
            await share_server_stop()


async def _sweep_at(expires_at: datetime) -> None:
    # Expiry is otherwise noticed only when someone requests the token, so
    # without this the listener outlives its last share.
    # Looped because the sleep clock and the wall clock can disagree by a hair,
    # and waking just early would leave the share unexpired and never revisited.
    while (expires_at - datetime.now(timezone.utc)).total_seconds() > 0:
        delay = (expires_at - datetime.now(timezone.utc)).total_seconds()
        await asyncio.sleep(max(delay, 0.01))
    await share_util_sweep()


def _schedule_sweep(expires_at: datetime) -> None:
    timer = asyncio.create_task(_sweep_at(expires_at))
    _expiry_timers.add(timer)
    timer.add_done_callback(_expiry_timers.discard)


async def share_util_create(
    album_id: str,
    expires_in_minutes: Optional[int] = None,
    password: Optional[str] = None,
) -> ShareEntry:
    """Issue a token for an album and make sure the listener is up."""
    async with _orchestration_lock:
        await share_server_start()
        entry = share_registry_create(
            album_id, expires_in_minutes=expires_in_minutes, password=password
        )
        if entry.expires_at is not None:
            _schedule_sweep(entry.expires_at)
        return entry


async def share_util_revoke(token: str) -> bool:
    """
    End one share, stopping the listener once nothing is being served.

    False means the token was already gone.
    """
    async with _orchestration_lock:
        if not share_registry_revoke(token):
            return False
        if share_registry_count() == 0:
            await share_server_stop()
        return True


def share_util_describe(entry: ShareEntry, port: int) -> ShareDescription:
    """
    Describe one share for the desktop UI.

    One URL per candidate interface rather than a single address: which one a
    phone can actually reach depends on the network, so the caller chooses.
    """
    album = db_get_album(entry.album_id)
    return {
        "token": entry.token,
        "album_id": entry.album_id,
        # An album deleted while shared leaves the token pointing at nothing;
        # the viewer 404s, so say so here rather than failing the listing.
        "album_name": album["album_name"] if album else "(deleted album)",
        "image_count": db_count_album_images(entry.album_id),
        "port": port,
        "created_at": entry.created_at.isoformat(),
        "expires_at": entry.expires_at.isoformat() if entry.expires_at else None,
        "is_protected": entry.is_protected,
        "urls": [
            {
                "interface": candidate.interface,
                "ip": candidate.ip,
                "url": f"http://{candidate.ip}:{port}/s/{entry.token}",
            }
            for candidate in network_util_list_candidates()
        ],
    }
