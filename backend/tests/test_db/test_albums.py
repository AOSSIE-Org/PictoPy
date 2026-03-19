import os
import sqlite3
import sys
import uuid

import pytest

from backend.app.config.settings import DATABASE_PATH
from backend.app.database.albums import verify_album_password, db_insert_album, db_delete_album, db_get_album, \
    db_update_album, db_get_all_albums, db_get_album_by_name, db_get_album_images, db_add_images_to_album

@pytest.fixture
def setup_test_db(monkeypatch):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS albums")

    cursor.execute("""
        CREATE TABLE albums (
            album_id TEXT PRIMARY KEY,
            album_name TEXT,
            description TEXT,
            is_hidden INTEGER,
            password_hash TEXT
        )
    """)

    conn.commit()
    conn.close()

    yield

def test_insert_and_get_album(setup_test_db):
    album_id = str(uuid.uuid4())
    album_name = f"Test Album"

    db_insert_album(
        album_id,
        album_name,
        "description",
        False
    )

    album = db_get_album(album_id)

    assert album is not None
    assert album[0] == album_id
    assert album[1] == album_name

def test_get_album_by_name(setup_test_db):

    album_id = str(uuid.uuid4())
    album_name = f"Test Album"

    db_insert_album(album_id, album_name, "")

    album = db_get_album_by_name(album_name)

    assert album is not None
    assert album[1] == album_name


def test_get_all_albums(setup_test_db):
    db_insert_album(str(uuid.uuid4()), "A1", "", False)
    db_insert_album(str(uuid.uuid4()), "A2", "", True)

    visible = db_get_all_albums()

    assert len(visible) == 1

    all_albums = db_get_all_albums(show_hidden=True)

    assert len(all_albums) == 2


def test_update_album(setup_test_db):

    album_id = str(uuid.uuid4())
    album_password_id=str(uuid.uuid4())
    db_insert_album(album_id, "Old", "")
    db_insert_album(album_password_id,"password","",password="123")
    db_update_album(
        album_id,
        "New Name",
        "New Description",
        True
    )
    db_update_album(
        album_password_id,
        "New Name2",
        "New Description2",
        True,
        password="123"
    )
    album = db_get_album(album_id)

    assert album[1] == "New Name"
    assert album[2] == "New Description"
    assert album[3] == 1

    album = db_get_album(album_password_id)
    assert album[1] == "New Name2"
    assert album[2] == "New Description2"
    assert album[3] == 1



def test_delete_album(setup_test_db):

    album_id = str(uuid.uuid4())

    db_insert_album(album_id, "Delete Me")

    db_delete_album(album_id)

    album = db_get_album(album_id)

    assert album is None


def test_verify_album_password(setup_test_db):

    album_id = str(uuid.uuid4())

    db_insert_album(
        album_id,
        "Protected",
        "",
        False,
        password="secret123"
    )

    assert verify_album_password(album_id, "secret123") is True
    assert verify_album_password(album_id, "wrong") is False
    assert verify_album_password("123", "wrong") is False
