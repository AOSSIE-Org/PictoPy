from datetime import datetime, timedelta, timezone
from typing import Iterator

import bcrypt
import pytest

from app.share.registry import (
    share_registry_clear,
    share_registry_count,
    share_registry_create,
    share_registry_get,
    share_registry_is_throttled,
    share_registry_is_unlocked,
    share_registry_list,
    share_registry_revoke,
    share_registry_unlock,
)

PASSWORD = "correct-horse-battery"


@pytest.fixture(autouse=True)
def empty_registry() -> Iterator[None]:
    """The registry is module state, so it has to be reset between tests."""
    share_registry_clear()
    yield
    share_registry_clear()


@pytest.fixture(autouse=True)
def cheap_hashing(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Hash at the minimum cost.

    bcrypt's default work factor is the point in production and pure waste here,
    where the tests only care that the algorithm is wired up correctly.
    """
    gensalt = bcrypt.gensalt
    monkeypatch.setattr(bcrypt, "gensalt", lambda: gensalt(4))


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


class TestPassword:
    def test_a_share_is_open_by_default(self) -> None:
        entry = share_registry_create("album-1")
        assert entry.is_protected is False
        assert share_registry_is_unlocked(entry, None) is True

    def test_only_a_hash_is_kept(self) -> None:
        """The plaintext must not survive anywhere on the entry."""
        entry = share_registry_create("album-1", password=PASSWORD)
        assert entry.is_protected is True
        assert entry.password_hash is not None
        assert PASSWORD.encode("utf-8") not in entry.password_hash

    def test_the_right_password_opens_the_share(self) -> None:
        entry = share_registry_create("album-1", password=PASSWORD)
        cookie = share_registry_unlock(entry, PASSWORD)
        assert cookie is not None
        assert share_registry_is_unlocked(entry, cookie) is True

    def test_the_wrong_password_does_not(self) -> None:
        entry = share_registry_create("album-1", password=PASSWORD)
        assert share_registry_unlock(entry, "guess") is None

    def test_a_protected_share_is_locked_without_a_cookie(self) -> None:
        entry = share_registry_create("album-1", password=PASSWORD)
        assert share_registry_is_unlocked(entry, None) is False
        assert share_registry_is_unlocked(entry, "forged") is False

    def test_a_cookie_does_not_carry_to_another_share(self) -> None:
        """
        The invariant that keeps one unlocked album from unlocking the rest,
        including a second share of the same album under the same password.
        """
        first = share_registry_create("album-1", password=PASSWORD)
        second = share_registry_create("album-1", password=PASSWORD)
        cookie = share_registry_unlock(first, PASSWORD)
        assert share_registry_is_unlocked(second, cookie) is False

    def test_an_open_share_cannot_be_unlocked(self) -> None:
        """Nothing to check against, so no cookie should ever be minted."""
        entry = share_registry_create("album-1")
        assert share_registry_unlock(entry, PASSWORD) is None

    def test_repeated_failures_stop_further_attempts(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr("app.share.registry._MAX_FAILED_UNLOCKS", 3)
        entry = share_registry_create("album-1", password=PASSWORD)

        for _ in range(3):
            assert share_registry_unlock(entry, "guess") is None

        assert share_registry_is_throttled(entry) is True
        # The cooldown has to bite regardless of what is guessed next, or it
        # would only be slowing an attacker down between wrong answers.
        assert share_registry_unlock(entry, PASSWORD) is None

    def test_getting_it_right_clears_earlier_failures(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr("app.share.registry._MAX_FAILED_UNLOCKS", 3)
        entry = share_registry_create("album-1", password=PASSWORD)

        share_registry_unlock(entry, "guess")
        share_registry_unlock(entry, "guess")
        assert share_registry_unlock(entry, PASSWORD) is not None

        share_registry_unlock(entry, "guess")
        share_registry_unlock(entry, "guess")
        assert share_registry_is_throttled(entry) is False

    def test_the_cooldown_expires(self) -> None:
        entry = share_registry_create("album-1", password=PASSWORD)
        entry.locked_until = datetime.now(timezone.utc) - timedelta(seconds=1)
        assert share_registry_is_throttled(entry) is False
        assert share_registry_unlock(entry, PASSWORD) is not None


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
