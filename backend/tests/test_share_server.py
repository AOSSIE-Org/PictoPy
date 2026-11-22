import asyncio
import socket
from datetime import datetime, timedelta, timezone
from typing import Iterator, List, Optional, Tuple

import pytest

from app.share import server as share_server
import app.utils.share as share_utils
from app.share.registry import (
    share_registry_clear,
    share_registry_count,
    share_registry_create,
)
from app.share.server import (
    share_server_is_running,
    share_server_port,
    share_server_start,
    share_server_stop,
)
from app.utils.share import share_util_create, share_util_revoke, share_util_sweep

# Every assertion about listener state is made inside the coroutine, because
# asyncio.run cancels the serve task and clears the state on its way out.


async def _wait_until_stopped(timeout: float = 2.0) -> None:
    """
    Give the done-callback time to run, without pinning a fixed delay.

    A sleep long enough to be safe on a loaded CI box is far longer than this
    ever needs locally, so poll the observable state and stop as soon as it
    settles. Returning on timeout lets the assertion report the real state.
    """
    deadline = asyncio.get_running_loop().time() + timeout
    while share_server_is_running() and asyncio.get_running_loop().time() < deadline:
        await asyncio.sleep(0.01)


@pytest.fixture(autouse=True)
def clean_lifecycle() -> Iterator[None]:
    """
    Reset the listener and both module-level locks between tests.

    Each test drives its own event loop, and an asyncio lock binds to the first
    loop that awaits it, so a lock carried across tests would raise about a
    different running loop.
    """
    import app.utils.share as share_utils

    share_registry_clear()
    share_server._clear()
    share_server._lifecycle_lock = asyncio.Lock()
    share_utils._orchestration_lock = asyncio.Lock()

    yield

    share_server._clear()
    share_registry_clear()


class TestLifecycle:
    def test_start_binds_and_reports_the_port(self) -> None:
        async def scenario() -> Tuple[int, int, bool]:
            port = await share_server_start()
            return port, share_server_port(), share_server_is_running()

        port, reported, running = asyncio.run(scenario())
        assert port == reported
        assert running is True

    def test_starting_twice_reuses_the_listener(self) -> None:
        async def scenario() -> Tuple[int, int]:
            return await share_server_start(), await share_server_start()

        first, second = asyncio.run(scenario())
        assert first == second

    def test_stop_is_safe_when_never_started(self) -> None:
        async def scenario() -> bool:
            await share_server_stop()
            return share_server_is_running()

        assert asyncio.run(scenario()) is False

    def test_stop_releases_the_port(self) -> None:
        async def scenario() -> Tuple[Optional[int], bool]:
            await share_server_start()
            await share_server_stop()
            return share_server_port(), share_server_is_running()

        port, running = asyncio.run(scenario())
        assert port is None
        assert running is False


class TestSupervision:
    def test_a_listener_that_dies_is_not_reported_as_running(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Without a done-callback the port stays set after serve() fails, and a
        share would be handed out for a socket nothing is accepting on.
        """

        async def boom(
            self: share_server._EmbeddedServer,
            sockets: Optional[List[socket.socket]] = None,
        ) -> None:
            raise RuntimeError("listener died")

        monkeypatch.setattr(share_server._EmbeddedServer, "serve", boom)

        async def scenario() -> Tuple[Optional[int], bool]:
            await share_server_start()
            await _wait_until_stopped()
            return share_server_port(), share_server_is_running()

        port, running = asyncio.run(scenario())
        assert port is None
        assert running is False


class TestRevokeOrchestration:
    def test_revoking_the_last_share_stops_the_listener(self) -> None:
        async def scenario() -> bool:
            await share_server_start()
            entry = share_registry_create("album-1")
            await share_util_revoke(entry.token)
            return share_server_is_running()

        assert asyncio.run(scenario()) is False

    def test_revoking_one_of_two_leaves_the_listener_up(self) -> None:
        async def scenario() -> bool:
            await share_server_start()
            first = share_registry_create("album-1")
            share_registry_create("album-2")
            await share_util_revoke(first.token)
            return share_server_is_running()

        assert asyncio.run(scenario()) is True

    def test_revoking_an_unknown_token_reports_false(self) -> None:
        assert asyncio.run(share_util_revoke("nope")) is False


class TestExpiryOrchestration:
    def test_sweeping_after_the_last_share_expires_stops_the_listener(self) -> None:
        async def scenario() -> Tuple[bool, int]:
            await share_server_start()
            entry = share_registry_create("album-1", expires_in_minutes=1)
            entry.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
            await share_util_sweep()
            return share_server_is_running(), share_registry_count()

        running, remaining = asyncio.run(scenario())
        assert running is False
        assert remaining == 0

    def test_sweeping_keeps_the_listener_while_a_share_is_live(self) -> None:
        async def scenario() -> bool:
            await share_server_start()
            expired = share_registry_create("album-1", expires_in_minutes=1)
            expired.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
            share_registry_create("album-2")
            await share_util_sweep()
            return share_server_is_running()

        assert asyncio.run(scenario()) is True

    def test_an_expiring_share_stops_the_listener_without_any_request(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        real_create = share_utils.share_registry_create

        # Only the deadline is shortened; scheduling is left to share_util_create.
        def short_lived(*args: object, **kwargs: object) -> object:
            entry = real_create(*args, **kwargs)
            entry.expires_at = datetime.now(timezone.utc) + timedelta(seconds=0.1)
            return entry

        monkeypatch.setattr(share_utils, "share_registry_create", short_lived)

        async def scenario() -> bool:
            await share_util_create("album-1", expires_in_minutes=1)
            # Poll for the outcome rather than guessing how long shutdown takes.
            for _ in range(100):
                if not share_server_is_running():
                    return False
                await asyncio.sleep(0.05)
            return True

        assert asyncio.run(scenario()) is False
