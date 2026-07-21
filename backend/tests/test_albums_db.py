import pytest
import sqlite3
import uuid
from unittest.mock import patch, MagicMock
from app.database.albums import (
    db_create_albums_table,
    db_create_album_images_table,
    db_get_all_albums,
    db_get_album_by_name,
    db_get_album,
    db_insert_album,
    db_update_album,
    db_delete_album,
    db_get_album_images,
    db_remove_images_from_album,
    verify_album_password,
)


class TestDbCreateAlbumsTable:
    # Tests that albums table is created without raising errors
    def test_create_albums_table_success(self):
        with patch("app.database.albums.sqlite3.connect") as mock_connect:
            mock_conn = MagicMock()
            mock_connect.return_value = mock_conn
            db_create_albums_table()
            mock_conn.cursor.return_value.execute.assert_called_once()
            mock_conn.commit.assert_called_once()

    # Tests that connection is closed even if an error occurs
    def test_create_albums_table_closes_connection_on_error(self):
        with patch("app.database.albums.sqlite3.connect") as mock_connect:
            mock_conn = MagicMock()
            mock_conn.cursor.return_value.execute.side_effect = sqlite3.Error("fail")
            mock_connect.return_value = mock_conn
            with pytest.raises(sqlite3.Error):
                db_create_albums_table()
            mock_conn.close.assert_called_once()


class TestDbCreateAlbumImagesTable:
    # Tests that album_images table is created without raising errors
    def test_create_album_images_table_success(self):
        with patch("app.database.albums.sqlite3.connect") as mock_connect:
            mock_conn = MagicMock()
            mock_connect.return_value = mock_conn
            db_create_album_images_table()
            mock_conn.cursor.return_value.execute.assert_called_once()
            mock_conn.commit.assert_called_once()
    
    # Tests that connection is closed even if an error occurs during table creation
    # def test_create_album_images_table_closes_connection_on_error(self):
    #     with patch("app.database.albums.sqlite3.connect") as mock_connect:
    #         mock_conn = MagicMock()
    #         mock_conn.cursor.return_value.execute.side_effect = sqlite3.Error("fail")
    #         mock_connect.return_value = mock_conn
    #         with pytest.raises(sqlite3.Error):
    #             db_create_album_images_table()
    #         mock_conn.close.assert_called_once()

    def test_create_album_images_table_closes_connection_on_error(self):
        with patch("app.database.albums.sqlite3.connect") as mock_connect:
            mock_conn = MagicMock()
            mock_conn.cursor.return_value.execute.side_effect = sqlite3.Error("fail")
            mock_connect.return_value = mock_conn
            with pytest.raises(sqlite3.Error):
                db_create_album_images_table()
            mock_conn.close.assert_called_once()

class TestDbGetAllAlbums:
    # Tests that all visible albums are returned when show_hidden is False
    def test_get_all_albums_public_only(self):
        fake_albums = [
            ("id-1", "Album One", "Desc 1", 0, None),
            ("id-2", "Album Two", "Desc 2", 0, None),
        ]
        with patch("app.database.albums.sqlite3.connect") as mock_connect:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = fake_albums
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn
            result = db_get_all_albums(show_hidden=False)
            assert result == fake_albums
            mock_cursor.execute.assert_called_once_with(
                "SELECT * FROM albums WHERE is_hidden = 0"
            )

    # Tests that hidden albums are also returned when show_hidden is True
    def test_get_all_albums_include_hidden(self):
        fake_albums = [
            ("id-1", "Album One", "Desc 1", 0, None),
            ("id-2", "Hidden Album", "Secret", 1, "hash"),
        ]
        with patch("app.database.albums.sqlite3.connect") as mock_connect:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = fake_albums
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn
            result = db_get_all_albums(show_hidden=True)
            assert result == fake_albums
            mock_cursor.execute.assert_called_once_with("SELECT * FROM albums")

    # Tests that an empty list is returned when no albums exist
    def test_get_all_albums_empty(self):
        with patch("app.database.albums.sqlite3.connect") as mock_connect:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = []
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn
            result = db_get_all_albums()
            assert result == []


class TestDbGetAlbumByName:
    # Tests that correct album is returned when name matches
    def test_get_album_by_name_found(self):
        fake_album = ("id-1", "Summer Trip", "Fun times", 0, None)
        with patch("app.database.albums.sqlite3.connect") as mock_connect:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = fake_album
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn
            result = db_get_album_by_name("Summer Trip")
            assert result == fake_album

    # Tests that None is returned when album name does not exist
    def test_get_album_by_name_not_found(self):
        with patch("app.database.albums.sqlite3.connect") as mock_connect:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = None
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn
            result = db_get_album_by_name("Nonexistent")
            assert result is None


class TestDbGetAlbum:
    # Tests that correct album is returned when album_id matches
    def test_get_album_found(self):
        album_id = str(uuid.uuid4())
        fake_album = (album_id, "My Album", "Description", 0, None)
        with patch("app.database.albums.sqlite3.connect") as mock_connect:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = fake_album
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn
            result = db_get_album(album_id)
            assert result == fake_album

    # Tests that None is returned when album_id does not exist
    def test_get_album_not_found(self):
        with patch("app.database.albums.sqlite3.connect") as mock_connect:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = None
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn
            result = db_get_album("nonexistent-id")
            assert result is None


class TestDbInsertAlbum:
    # Tests that a basic album without password is inserted correctly
    def test_insert_album_without_password(self):
        album_id = str(uuid.uuid4())
        with patch("app.database.albums.sqlite3.connect") as mock_connect:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn
            db_insert_album(album_id, "Test Album", "A description", False, None)
            mock_cursor.execute.assert_called_once()
            mock_conn.commit.assert_called_once()

    # Tests that a password is hashed before being stored in the database
    def test_insert_album_with_password_hashes_it(self):
        album_id = str(uuid.uuid4())
        with patch("app.database.albums.sqlite3.connect") as mock_connect:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn
            db_insert_album(album_id, "Secret Album", "Hidden", True, "mypassword")
            call_args = mock_cursor.execute.call_args[0][1]
            # password_hash should not be plain text
            assert call_args[4] != "mypassword"
            assert call_args[4] is not None


class TestDbUpdateAlbum:
    # Tests that album fields are updated correctly without changing password
    def test_update_album_without_password(self):
        album_id = str(uuid.uuid4())
        with patch("app.database.albums.sqlite3.connect") as mock_connect:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn
            db_update_album(album_id, "New Name", "New Desc", False, None)
            mock_cursor.execute.assert_called_once()
            mock_conn.commit.assert_called_once()

    # Tests that password is hashed when updating album with a new password
    def test_update_album_with_new_password(self):
        album_id = str(uuid.uuid4())
        with patch("app.database.albums.sqlite3.connect") as mock_connect:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn
            db_update_album(album_id, "New Name", "New Desc", True, "newpassword")
            call_args = mock_cursor.execute.call_args[0][1]
            assert call_args[3] != "newpassword"


class TestDbDeleteAlbum:
    # Tests that delete is called with the correct album_id
    def test_delete_album_success(self):
        album_id = str(uuid.uuid4())
        with patch("app.database.albums.get_db_connection") as mock_conn_ctx:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_conn_ctx.return_value.__enter__ = MagicMock(return_value=mock_conn)
            mock_conn_ctx.return_value.__exit__ = MagicMock(return_value=False)
            db_delete_album(album_id)
            mock_cursor.execute.assert_called_once_with(
                "DELETE FROM albums WHERE album_id = ?", (album_id,)
            )


class TestDbGetAlbumImages:
    # Tests that list of image IDs is returned for a valid album
    def test_get_album_images_returns_list(self):
        album_id = str(uuid.uuid4())
        fake_images = [("img-1",), ("img-2",), ("img-3",)]
        with patch("app.database.albums.sqlite3.connect") as mock_connect:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = fake_images
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn
            result = db_get_album_images(album_id)
            assert result == ["img-1", "img-2", "img-3"]

    # Tests that empty list is returned when album has no images
    def test_get_album_images_empty(self):
        album_id = str(uuid.uuid4())
        with patch("app.database.albums.sqlite3.connect") as mock_connect:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = []
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn
            result = db_get_album_images(album_id)
            assert result == []


class TestDbRemoveImagesFromAlbum:
    # Tests that multiple images are removed from album in one call
    def test_remove_images_from_album(self):
        album_id = str(uuid.uuid4())
        image_ids = ["img-1", "img-2"]
        with patch("app.database.albums.sqlite3.connect") as mock_connect:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn
            db_remove_images_from_album(album_id, image_ids)
            mock_cursor.executemany.assert_called_once()
            mock_conn.commit.assert_called_once()


class TestVerifyAlbumPassword:
    # Tests that correct password returns True
    def test_verify_correct_password(self):
        import bcrypt
        album_id = str(uuid.uuid4())
        password = "securepass"
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        with patch("app.database.albums.sqlite3.connect") as mock_connect:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = (hashed,)
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn
            result = verify_album_password(album_id, password)
            assert result is True

    # Tests that wrong password returns False
    def test_verify_wrong_password(self):
        import bcrypt
        album_id = str(uuid.uuid4())
        hashed = bcrypt.hashpw("correct".encode(), bcrypt.gensalt()).decode()
        with patch("app.database.albums.sqlite3.connect") as mock_connect:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = (hashed,)
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn
            result = verify_album_password(album_id, "wrongpass")
            assert result is False

    # Tests that missing album returns False without error
    def test_verify_album_not_found_returns_false(self):
        album_id = str(uuid.uuid4())
        with patch("app.database.albums.sqlite3.connect") as mock_connect:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = None
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn
            result = verify_album_password(album_id, "anypassword")
            assert result is False