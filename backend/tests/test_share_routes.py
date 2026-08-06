import os
import sqlite3
import tempfile
from datetime import datetime, timedelta, timezone
from typing import Iterator, List

import pytest
from fastapi.testclient import TestClient

from app.database.albums import (
    db_create_album_images_table,
    db_create_albums_table,
    db_insert_album,
)
from app.database.images import db_create_images_table
from app.share.app import create_share_app
from app.share.registry import (
    share_registry_clear,
    share_registry_create,
    share_registry_get,
    share_registry_revoke,
)

JPEG_BYTES = b"\xff\xd8\xff\xe0fake-jpeg-body\xff\xd9"
THUMB_BYTES = b"\xff\xd8\xff\xe0fake-thumb-body\xff\xd9"


@pytest.fixture
def share_env(monkeypatch: pytest.MonkeyPatch, tmp_path) -> Iterator[dict]:
    """A share server backed by a throwaway database and real image files."""
    db_fd, db_path = tempfile.mkstemp()
    os.close(db_fd)

    monkeypatch.setattr("app.config.settings.DATABASE_PATH", db_path)
    monkeypatch.setattr("app.database.albums.DATABASE_PATH", db_path)
    monkeypatch.setattr("app.database.images.DATABASE_PATH", db_path)
    monkeypatch.setattr("app.database.connection.DATABASE_PATH", db_path)

    db_create_albums_table()
    db_create_album_images_table()
    db_create_images_table()

    share_registry_clear()

    def add_image(image_id: str) -> None:
        photo = tmp_path / f"{image_id}.jpg"
        thumb = tmp_path / f"{image_id}_thumb.jpg"
        photo.write_bytes(JPEG_BYTES)
        thumb.write_bytes(THUMB_BYTES)
        conn = sqlite3.connect(db_path)
        conn.execute(
            "INSERT INTO images (id, path, thumbnailPath) VALUES (?, ?, ?)",
            (image_id, str(photo), str(thumb)),
        )
        conn.commit()
        conn.close()

    def link(album_id: str, image_ids: List[str]) -> None:
        conn = sqlite3.connect(db_path)
        conn.executemany(
            "INSERT INTO album_images (album_id, image_id) VALUES (?, ?)",
            [(album_id, image_id) for image_id in image_ids],
        )
        conn.commit()
        conn.close()

    db_insert_album("album-1", "Trip to Goa", "", False, None)
    db_insert_album("album-2", "Private", "", False, None)
    for image_id in ("img-1", "img-2", "other-1"):
        add_image(image_id)
    link("album-1", ["img-1", "img-2"])
    link("album-2", ["other-1"])

    entry = share_registry_create("album-1")

    with TestClient(create_share_app()) as client:
        yield {
            "client": client,
            "token": entry.token,
            "tmp_path": tmp_path,
            "db_path": db_path,
        }

    share_registry_clear()
    os.unlink(db_path)


def expire(token: str) -> None:
    share_registry_get(token).expires_at = datetime.now(timezone.utc) - timedelta(
        seconds=1
    )


class TestViewer:
    def test_renders_the_album(self, share_env):
        response = share_env["client"].get(f"/s/{share_env['token']}")
        assert response.status_code == 200
        assert "Trip to Goa" in response.text
        assert "2 photos" in response.text

    def test_links_every_image_in_the_album(self, share_env):
        response = share_env["client"].get(f"/s/{share_env['token']}")
        assert "img-1" in response.text
        assert "img-2" in response.text

    def test_does_not_link_images_from_other_albums(self, share_env):
        response = share_env["client"].get(f"/s/{share_env['token']}")
        assert "other-1" not in response.text

    def test_never_exposes_a_filesystem_path(self, share_env):
        """The receiver works in IDs; leaking paths would map the host's disk."""
        response = share_env["client"].get(f"/s/{share_env['token']}")
        assert str(share_env["tmp_path"]) not in response.text
        assert ".jpg" not in response.text


class TestTokenLifecycle:
    def test_unknown_token_is_404(self, share_env):
        assert share_env["client"].get("/s/made-up-token").status_code == 404

    def test_revoked_token_is_404(self, share_env):
        share_registry_revoke(share_env["token"])
        assert share_env["client"].get(f"/s/{share_env['token']}").status_code == 404

    def test_expired_token_is_404(self, share_env):
        expire(share_env["token"])
        assert share_env["client"].get(f"/s/{share_env['token']}").status_code == 404

    def test_revoked_token_cannot_still_fetch_media(self, share_env):
        share_registry_revoke(share_env["token"])
        response = share_env["client"].get(f"/s/{share_env['token']}/photo/img-1")
        assert response.status_code == 404


class TestMedia:
    def test_serves_the_thumbnail_for_the_grid(self, share_env):
        response = share_env["client"].get(f"/s/{share_env['token']}/thumb/img-1")
        assert response.status_code == 200
        assert response.content == THUMB_BYTES

    def test_serves_the_original_for_full_view(self, share_env):
        response = share_env["client"].get(f"/s/{share_env['token']}/photo/img-1")
        assert response.status_code == 200
        assert response.content == JPEG_BYTES

    def test_image_from_another_album_is_refused(self, share_env):
        """
        The invariant that keeps a share token from being a read handle over
        every image PictoPy has indexed.
        """
        response = share_env["client"].get(f"/s/{share_env['token']}/photo/other-1")
        assert response.status_code == 404

    def test_unknown_image_id_is_404(self, share_env):
        response = share_env["client"].get(f"/s/{share_env['token']}/photo/nope")
        assert response.status_code == 404

    def test_missing_file_on_disk_is_404(self, share_env):
        (share_env["tmp_path"] / "img-1.jpg").unlink()
        response = share_env["client"].get(f"/s/{share_env['token']}/photo/img-1")
        assert response.status_code == 404


class TestViewerChrome:
    def test_thumbnails_are_lazy(self, share_env):
        """Tiles carry data-src so a large album does not fetch every photo."""
        body = share_env["client"].get(f"/s/{share_env['token']}").text
        assert 'data-src="/s/' in body
        assert body.count("data-src=") == 2

    def test_lightbox_and_filmstrip_are_present(self, share_env):
        body = share_env["client"].get(f"/s/{share_env['token']}").text
        assert 'id="lightbox"' in body
        assert 'id="filmstrip"' in body
        assert body.count('class="filmstrip-thumb"') == 2

    def test_theme_control_is_present(self, share_env):
        body = share_env["client"].get(f"/s/{share_env['token']}").text
        for choice in ('data-theme="auto"', 'data-theme="light"', 'data-theme="dark"'):
            assert choice in body

    def test_no_external_resources(self, share_env):
        """
        The page has to render on a network with no route to the internet — a
        hotspot between two devices is the fallback when the LAN blocks peers.
        """
        body = share_env["client"].get(f"/s/{share_env['token']}").text
        assert "http://" not in body.replace("http://www.w3.org", "")
        assert "https://" not in body.replace("https://www.w3.org", "")

    def test_expiry_is_shown_only_when_set(self, share_env):
        assert "Expires" not in share_env["client"].get(f"/s/{share_env['token']}").text

        entry = share_registry_create("album-1", expires_in_minutes=30)
        body = share_env["client"].get(f"/s/{entry.token}").text
        assert "Expires" in body
        assert entry.expires_at.isoformat() in body

    def test_album_name_is_escaped(self, share_env):
        """An album named after a script tag must not become one."""
        conn = sqlite3.connect(share_env["db_path"])
        conn.execute(
            "UPDATE albums SET album_name = ? WHERE album_id = ?",
            ("<script>alert(1)</script>", "album-1"),
        )
        conn.commit()
        conn.close()

        body = share_env["client"].get(f"/s/{share_env['token']}").text
        assert "<script>alert(1)</script>" not in body
        assert "&lt;script&gt;" in body


class TestSurface:
    def test_docs_are_not_exposed(self, share_env):
        """The share app is public; its route list should not be enumerable."""
        client = share_env["client"]
        assert client.get("/docs").status_code == 404
        assert client.get("/openapi.json").status_code == 404

    def test_main_backend_routes_are_absent(self, share_env):
        client = share_env["client"]
        for path in ("/health", "/albums/", "/images/", "/shutdown"):
            assert client.get(path).status_code == 404
