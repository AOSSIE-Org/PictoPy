from datetime import datetime, timedelta, timezone
from typing import Iterator

import pytest

from app.share.registry import (
    share_registry_clear,
    share_registry_count,
    share_registry_create,
    share_registry_get,
    share_registry_list,
    share_registry_revoke,
)


@pytest.fixture(autouse=True)
def empty_registry() -> Iterator[None]:
    """The registry is module state, so it has to be reset between tests."""
    share_registry_clear()
    yield
    share_registry_clear()


def expire(token: str) -> None:
    """Backdate a share's expiry so lookups treat it as stale."""
    entry = share_registry_get(token)
    assert entry is not None
    entry.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)


class TestCreate:
    def test_returns_a_live_entry(self) -> None:
        entry = share_registry_create("album-1")
        assert entry.album_id == "album-1"
        assert share_registry_get(entry.token) is entry

    def test_tokens_are_unguessable_and_unique(self) -> None:
        tokens = {share_registry_create("album-1").token for _ in range(50)}
        assert len(tokens) == 50
        # token_urlsafe(32) is 43 characters; anything shorter means the token
        # size regressed, which is the whole protection for a shared album.
        assert all(len(token) >= 43 for token in tokens)

    def test_no_expiry_by_default(self) -> None:
        assert share_registry_create("album-1").expires_at is None

    def test_sharing_twice_leaves_both_valid(self) -> None:
        first = share_registry_create("album-1")
        second = share_registry_create("album-1")
        assert first.token != second.token
        assert share_registry_get(first.token) is not None
        assert share_registry_get(second.token) is not None


class TestLookup:
    def test_unknown_token_is_none(self) -> None:
        assert share_registry_get("nope") is None

    def test_expired_token_is_none(self) -> None:
        entry = share_registry_create("album-1", expires_in_minutes=5)
        expire(entry.token)
        assert share_registry_get(entry.token) is None

    def test_expired_token_is_dropped_not_just_hidden(self) -> None:
        entry = share_registry_create("album-1", expires_in_minutes=5)
        expire(entry.token)
        share_registry_get(entry.token)
        assert share_registry_count() == 0

    def test_unexpired_token_survives(self) -> None:
        entry = share_registry_create("album-1", expires_in_minutes=60)
        assert share_registry_get(entry.token) is not None


class TestRevoke:
    def test_revoking_removes_the_share(self) -> None:
        entry = share_registry_create("album-1")
        assert share_registry_revoke(entry.token) is True
        assert share_registry_get(entry.token) is None

    def test_revoking_twice_reports_the_second_as_absent(self) -> None:
        entry = share_registry_create("album-1")
        share_registry_revoke(entry.token)
        assert share_registry_revoke(entry.token) is False

    def test_revoking_leaves_other_shares_alone(self) -> None:
        keep = share_registry_create("album-1")
        drop = share_registry_create("album-2")
        share_registry_revoke(drop.token)
        assert share_registry_get(keep.token) is not None


class TestListing:
    def test_lists_newest_first(self) -> None:
        older = share_registry_create("album-1")
        older.created_at -= timedelta(minutes=5)
        newer = share_registry_create("album-2")
        assert [e.token for e in share_registry_list()] == [newer.token, older.token]

    def test_expired_shares_are_omitted(self) -> None:
        live = share_registry_create("album-1")
        dead = share_registry_create("album-2", expires_in_minutes=5)
        expire(dead.token)
        assert [e.token for e in share_registry_list()] == [live.token]

    def test_count_tracks_live_shares(self) -> None:
        assert share_registry_count() == 0
        share_registry_create("album-1")
        share_registry_create("album-2")
        assert share_registry_count() == 2
