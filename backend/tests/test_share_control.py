"""
The localhost control surface: what the desktop UI sends and is told back.

The public viewer is covered separately in test_share_routes.py.
"""

import os
import tempfile
from typing import Iterator

import bcrypt
import pytest
from pydantic import ValidationError

from app.database.albums import (
    db_create_album_images_table,
    db_create_albums_table,
    db_insert_album,
)
from app.schemas.share import CreateShareRequest, Share
from app.share.registry import (
    PASSWORD_MAX_BYTES,
    share_registry_clear,
    share_registry_create,
)
from app.utils.share import share_util_describe

PORT = 52125


@pytest.fixture(autouse=True)
def cheap_hashing(monkeypatch: pytest.MonkeyPatch) -> None:
    """bcrypt's default work factor is the point in production, waste here."""
    gensalt = bcrypt.gensalt
    monkeypatch.setattr(bcrypt, "gensalt", lambda: gensalt(4))


@pytest.fixture(autouse=True)
def album_db(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """One album in a throwaway database, which is all describing a share reads."""
    db_fd, db_path = tempfile.mkstemp()
    os.close(db_fd)
    monkeypatch.setattr("app.database.albums.DATABASE_PATH", db_path)
    monkeypatch.setattr("app.database.connection.DATABASE_PATH", db_path)

    db_create_albums_table()
    db_create_album_images_table()
    db_insert_album("album-1", "Trip to Goa", "", False, None)
    share_registry_clear()

    yield

    share_registry_clear()
    os.unlink(db_path)


class TestDescription:
    def test_an_open_share_is_reported_as_open(self) -> None:
        entry = share_registry_create("album-1")
        assert share_util_describe(entry, PORT)["is_protected"] is False

    def test_a_protected_share_is_flagged(self) -> None:
        entry = share_registry_create("album-1", password="hunter-two-two")
        assert share_util_describe(entry, PORT)["is_protected"] is True

    def test_the_description_fills_the_response_model(self) -> None:
        """
        Catches the two halves of a share drifting apart: the TypedDict the
        backend builds and the model the UI is promised.
        """
        entry = share_registry_create("album-1", password="hunter-two-two")
        share = Share(**share_util_describe(entry, PORT))
        assert share.token == entry.token
        assert share.is_protected is True

    def test_no_password_material_is_returned(self) -> None:
        entry = share_registry_create("album-1", password="hunter-two-two")
        described = share_util_describe(entry, PORT)
        assert "password" not in described
        assert "hunter-two-two" not in str(described)


class TestCreateRequest:
    def test_password_is_optional(self) -> None:
        assert CreateShareRequest().password is None

    def test_a_trivial_password_is_rejected(self) -> None:
        with pytest.raises(ValidationError):
            CreateShareRequest(password="ab")

    def test_a_password_past_the_bcrypt_limit_is_rejected(self) -> None:
        """
        Silently truncating at 72 bytes would set a password the user never
        typed, so it has to be refused at the door.
        """
        with pytest.raises(ValidationError):
            CreateShareRequest(password="a" * (PASSWORD_MAX_BYTES + 1))

    def test_the_limit_counts_bytes_not_characters(self) -> None:
        # Well under 72 characters, comfortably over 72 bytes.
        with pytest.raises(ValidationError):
            CreateShareRequest(password="é" * 40)
