import sqlite3
import uuid

import pytest

from backend.app.config.settings import DATABASE_PATH
from backend.app.database.albums import db_insert_album, db_get_album_images, db_add_images_to_album, \
    db_remove_image_from_album, db_remove_images_from_album
from backend.app.database.images import db_bulk_insert_images, ImageRecord, db_get_all_images


@pytest.fixture
def setup_test_db(monkeypatch):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS images")

    cursor.execute("""
        -- auto-generated definition
    create table images
    (
        id            TEXT
            primary key,
        path          VARCHAR
            unique,
        folder_id     INTEGER
            references folders
                on delete cascade,
        thumbnailPath TEXT
            unique,
        metadata      TEXT,
        isTagged      BOOLEAN default 0,
        isFavourite   BOOLEAN default 0,
        latitude      REAL,
        longitude     REAL,
        captured_at   DATETIME
    );
    """)

    conn.commit()
    conn.close()

    yield


def test_get_and_remove_album_images(setup_test_db):
    album_id = str(uuid.uuid4())
    album_name = "Test Album"

    db_insert_album(album_id, album_name, "")
    with pytest.raises(ValueError, match="None of the provided image IDs exist in the database."):
        db_add_images_to_album(
            album_id,
            image_ids=["ced4be84-4e16-4c1b-a9c1-b7f2e2ee8494"]
        )
    img = {
        "id": "ced4be84-4e16-4c1b-a9c1-b7f2e2ee8494",
        "path": "C:\\Users\\user123\\Pictures\\Acer\\Acer_Wallpaper_01_5000x2814.jpg",
        "folder_id": "e6d83d84-ad5f-4901-9519-2a1be50977d7",
        "thumbnailPath": "C:\\Users\\user123\\AppData\\Local\\PictoPy\\PictoPy\\thumbnails\\thumbnail_ced4be84.jpg",
        "metadata": '{"name": "Acer_Wallpaper_01_5000x2814.jpg"}',
        "isTagged": 0,
        "latitude": None,
        "longitude": None,
        "captured_at": "2020-10-21T08:36:00",
    }
    db_bulk_insert_images([img])

    db_add_images_to_album(album_id, image_ids=["ced4be84-4e16-4c1b-a9c1-b7f2e2ee8494"])

    image = db_get_album_images(album_id)

    assert image[0]=="ced4be84-4e16-4c1b-a9c1-b7f2e2ee8494"

    with pytest.raises(ValueError, match="Image not found in the specified album"):
        db_remove_image_from_album(
            album_id,
            image_id="tmp"
        )
    db_remove_image_from_album(album_id, image[0])
    image = db_get_album_images(album_id)
    assert image ==[]

    img1 = {
        "id": "ced4be84-4e16-4c1b-a9c1-b7f2e2ee8494",
        "path": "C:\\Users\\user123\\Pictures\\Acer\\Acer_Wallpaper_01_5000x2814.jpg",
        "folder_id": "e6d83d84-ad5f-4901-9519-2a1be50977d7",
        "thumbnailPath": "C:\\Users\\user123\\AppData\\Local\\PictoPy\\PictoPy\\thumbnails\\thumbnail_ced4be84.jpg",
        "metadata": '{"name": "Acer_Wallpaper_01_5000x2814.jpg"}',
        "isTagged": 0,
        "latitude": None,
        "longitude": None,
        "captured_at": "2020-10-21T08:36:00",
    }
    img2 = {
        "id": "f423c320-080e-4d93-832f-2c2ccfd249ec",
        "path": "C:\\Users\\user123\\Pictures\\Acer\\Acer_Wallpaper_02_5000x2813.jpg",
        "folder_id": "e6d83d84-ad5f-4901-9519-2a1be50977d7",
        "thumbnailPath": "C:\\Users\\user123\\AppData\\Local\\PictoPy\\PictoPy\\thumbnails\\thumbnail_ced4be84.jpg",
        "metadata": '{"name": "Acer_Wallpaper_02_5000x2813.jpg"}',
        "isTagged": 0,
        "latitude": None,
        "longitude": None,
        "captured_at": "2020-10-21T08:36:00",
    }
    db_bulk_insert_images([img1,img2])
    db_add_images_to_album(album_id, image_ids=["ced4be84-4e16-4c1b-a9c1-b7f2e2ee8494","f423c320-080e-4d93-832f-2c2ccfd249ec"])
    db_remove_images_from_album(album_id, image_ids=["ced4be84-4e16-4c1b-a9c1-b7f2e2ee8494","f423c320-080e-4d93-832f-2c2ccfd249ec"])
    image = db_get_album_images(album_id)
    assert image ==[]

