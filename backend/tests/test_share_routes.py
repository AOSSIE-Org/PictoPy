import io
import os
import sqlite3
import tempfile
from datetime import datetime, timedelta, timezone
from email.utils import formatdate
from pathlib import Path
from typing import Dict, Iterator, List, TypedDict

import bcrypt
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.database.albums import (
    db_create_album_images_table,
    db_create_albums_table,
    db_insert_album,
)
from app.database.images import db_create_images_table
from app.share.app import create_share_app
from app.utils.xmp import FaceRecord, PictoPyMetadata, write_image_metadata
from app.utils.xmp.containers.png import PngContainer
from tests.test_xmp_stripping import _photo
from app.share.registry import (
    share_registry_clear,
    share_registry_create,
    share_registry_get,
    share_registry_revoke,
)

JPEG_BYTES = b"\xff\xd8\xff\xe0fake-jpeg-body\xff\xd9"
THUMB_BYTES = b"\xff\xd8\xff\xe0fake-thumb-body\xff\xd9"
PASSWORD = "correct-horse-battery"


@pytest.fixture(autouse=True)
def cheap_hashing(monkeypatch: pytest.MonkeyPatch) -> None:
    """bcrypt's default work factor is the point in production, waste here."""
    gensalt = bcrypt.gensalt
    monkeypatch.setattr(bcrypt, "gensalt", lambda: gensalt(4))


class ShareEnv(TypedDict):
    """What the share_env fixture hands each test."""

    client: TestClient
    token: str
    tmp_path: Path
    db_path: str


@pytest.fixture
def share_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[ShareEnv]:
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
    entry = share_registry_get(token)
    assert entry is not None
    entry.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)


class TestViewer:
    def test_renders_the_album(self, share_env: ShareEnv) -> None:
        response = share_env["client"].get(f"/s/{share_env['token']}")
        assert response.status_code == 200
        assert "Trip to Goa" in response.text
        assert "2 photos" in response.text

    def test_links_every_image_in_the_album(self, share_env: ShareEnv) -> None:
        response = share_env["client"].get(f"/s/{share_env['token']}")
        assert "img-1" in response.text
        assert "img-2" in response.text

    def test_does_not_link_images_from_other_albums(self, share_env: ShareEnv) -> None:
        response = share_env["client"].get(f"/s/{share_env['token']}")
        assert "other-1" not in response.text

    def test_never_exposes_a_filesystem_path(self, share_env: ShareEnv) -> None:
        """The receiver works in IDs; leaking paths would map the host's disk."""
        response = share_env["client"].get(f"/s/{share_env['token']}")
        assert str(share_env["tmp_path"]) not in response.text
        assert ".jpg" not in response.text


class TestTokenLifecycle:
    def test_unknown_token_is_404(self, share_env: ShareEnv) -> None:
        assert share_env["client"].get("/s/made-up-token").status_code == 404

    def test_revoked_token_is_404(self, share_env: ShareEnv) -> None:
        share_registry_revoke(share_env["token"])
        assert share_env["client"].get(f"/s/{share_env['token']}").status_code == 404

    def test_expired_token_is_404(self, share_env: ShareEnv) -> None:
        expire(share_env["token"])
        assert share_env["client"].get(f"/s/{share_env['token']}").status_code == 404

    def test_revoked_token_cannot_still_fetch_media(self, share_env: ShareEnv) -> None:
        share_registry_revoke(share_env["token"])
        response = share_env["client"].get(f"/s/{share_env['token']}/photo/img-1")
        assert response.status_code == 404


class TestMedia:
    def test_serves_the_thumbnail_for_the_grid(self, share_env: ShareEnv) -> None:
        response = share_env["client"].get(f"/s/{share_env['token']}/thumb/img-1")
        assert response.status_code == 200
        assert response.content == THUMB_BYTES

    def test_serves_the_original_for_full_view(self, share_env: ShareEnv) -> None:
        response = share_env["client"].get(f"/s/{share_env['token']}/photo/img-1")
        assert response.status_code == 200
        assert response.content == JPEG_BYTES

    def test_png_is_served_without_pictopy_metadata(self, share_env: ShareEnv) -> None:
        """Exported face embeddings and names stay home; everything else goes."""
        photo = share_env["tmp_path"] / "img-1.png"
        Image.new("RGB", (32, 24), (200, 30, 90)).save(photo)
        foreign = (
            b'<x:xmpmeta xmlns:x="adobe:ns:meta/"><rdf:RDF '
            b'xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
            b'<rdf:Description rdf:about="" '
            b'xmlns:dc="http://purl.org/dc/elements/1.1/">'
            b"<dc:creator>Someone</dc:creator></rdf:Description>"
            b"</rdf:RDF></x:xmpmeta>"
        )
        PngContainer().write_xmp(str(photo), foreign)
        write_image_metadata(
            str(photo),
            PictoPyMetadata(
                faces=[FaceRecord(embedding=[0.5] * 128, cluster_name="Ann")],
                albums=["Trip to Goa"],
            ),
        )
        on_disk = photo.read_bytes()
        assert b"pictopy" in on_disk and b"Ann" in on_disk
        conn = sqlite3.connect(share_env["db_path"])
        conn.execute("UPDATE images SET path = ? WHERE id = 'img-1'", (str(photo),))
        conn.commit()
        conn.close()

        response = share_env["client"].get(f"/s/{share_env['token']}/photo/img-1")
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"
        assert int(response.headers["content-length"]) == len(response.content)
        assert b"pictopy" not in response.content
        assert b"Ann" not in response.content
        assert b"<dc:creator>Someone</dc:creator>" in response.content
        assert (
            Image.open(io.BytesIO(response.content)).tobytes()
            == Image.open(photo).tobytes()
        )
        assert photo.read_bytes() == on_disk

    def test_image_from_another_album_is_refused(self, share_env: ShareEnv) -> None:
        """
        The invariant that keeps a share token from being a read handle over
        every image PictoPy has indexed.
        """
        response = share_env["client"].get(f"/s/{share_env['token']}/photo/other-1")
        assert response.status_code == 404

    def test_unknown_image_id_is_404(self, share_env: ShareEnv) -> None:
        response = share_env["client"].get(f"/s/{share_env['token']}/photo/nope")
        assert response.status_code == 404

    def test_missing_file_on_disk_is_404(self, share_env: ShareEnv) -> None:
        (share_env["tmp_path"] / "img-1.jpg").unlink()
        response = share_env["client"].get(f"/s/{share_env['token']}/photo/img-1")
        assert response.status_code == 404


class TestViewerChrome:
    def test_thumbnails_are_lazy(self, share_env: ShareEnv) -> None:
        """Tiles carry data-src so a large album does not fetch every photo."""
        body = share_env["client"].get(f"/s/{share_env['token']}").text
        assert 'data-src="/s/' in body
        assert body.count("data-src=") == 2

    def test_lightbox_and_filmstrip_are_present(self, share_env: ShareEnv) -> None:
        body = share_env["client"].get(f"/s/{share_env['token']}").text
        assert 'id="lightbox"' in body
        assert 'id="filmstrip"' in body
        assert body.count('class="filmstrip-thumb"') == 2

    def test_theme_control_is_present(self, share_env: ShareEnv) -> None:
        body = share_env["client"].get(f"/s/{share_env['token']}").text
        for choice in ('data-theme="auto"', 'data-theme="light"', 'data-theme="dark"'):
            assert choice in body

    def test_no_external_resources(self, share_env: ShareEnv) -> None:
        """
        The page has to render on a network with no route to the internet — a
        hotspot between two devices is the fallback when the LAN blocks peers.
        """
        body = share_env["client"].get(f"/s/{share_env['token']}").text
        assert "http://" not in body.replace("http://www.w3.org", "")
        assert "https://" not in body.replace("https://www.w3.org", "")

    def test_expiry_is_shown_only_when_set(self, share_env: ShareEnv) -> None:
        assert "Expires" not in share_env["client"].get(f"/s/{share_env['token']}").text

        entry = share_registry_create("album-1", expires_in_minutes=30)
        body = share_env["client"].get(f"/s/{entry.token}").text
        assert "Expires" in body
        assert entry.expires_at.isoformat() in body

    def test_album_name_is_escaped(self, share_env: ShareEnv) -> None:
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


class TestPasswordGate:
    def test_a_protected_share_asks_for_the_password(self, share_env: ShareEnv) -> None:
        entry = share_registry_create("album-1", password=PASSWORD)
        response = share_env["client"].get(f"/s/{entry.token}")
        assert response.status_code == 200
        assert 'name="password"' in response.text

    def test_the_gate_says_nothing_about_the_album(self, share_env: ShareEnv) -> None:
        """
        A link that reaches the wrong person should tell them only that some
        album exists — not its name, its size, or any of its photos.
        """
        entry = share_registry_create("album-1", password=PASSWORD)
        body = share_env["client"].get(f"/s/{entry.token}").text
        assert "Trip to Goa" not in body
        assert "2 photos" not in body
        assert "img-1" not in body

    def test_media_is_refused_while_locked(self, share_env: ShareEnv) -> None:
        entry = share_registry_create("album-1", password=PASSWORD)
        client = share_env["client"]
        assert client.get(f"/s/{entry.token}/thumb/img-1").status_code == 404
        assert client.get(f"/s/{entry.token}/photo/img-1").status_code == 404

    def test_the_right_password_opens_the_album(self, share_env: ShareEnv) -> None:
        entry = share_registry_create("album-1", password=PASSWORD)
        client = share_env["client"]

        response = client.post(
            f"/s/{entry.token}/unlock",
            data={"password": PASSWORD},
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert response.headers["location"] == f"/s/{entry.token}"

        assert "Trip to Goa" in client.get(f"/s/{entry.token}").text
        assert client.get(f"/s/{entry.token}/photo/img-1").status_code == 200

    def test_the_wrong_password_is_refused(self, share_env: ShareEnv) -> None:
        entry = share_registry_create("album-1", password=PASSWORD)
        client = share_env["client"]

        response = client.post(
            f"/s/{entry.token}/unlock",
            data={"password": "guess"},
            follow_redirects=False,
        )
        assert response.status_code == 401
        assert 'name="password"' in response.text
        assert "Trip to Goa" not in client.get(f"/s/{entry.token}").text

    def test_unlocking_one_share_leaves_the_others_locked(
        self, share_env: ShareEnv
    ) -> None:
        opened = share_registry_create("album-1", password=PASSWORD)
        other = share_registry_create("album-1", password=PASSWORD)
        client = share_env["client"]

        client.post(f"/s/{opened.token}/unlock", data={"password": PASSWORD})

        assert 'name="password"' in client.get(f"/s/{other.token}").text
        assert client.get(f"/s/{other.token}/photo/img-1").status_code == 404

    def test_an_open_share_needs_no_unlocking(self, share_env: ShareEnv) -> None:
        response = share_env["client"].post(
            f"/s/{share_env['token']}/unlock",
            data={"password": "anything"},
            follow_redirects=False,
        )
        assert response.status_code == 303

    def test_unlocking_an_unknown_token_is_404(self, share_env: ShareEnv) -> None:
        response = share_env["client"].post(
            "/s/made-up-token/unlock", data={"password": PASSWORD}
        )
        assert response.status_code == 404


class TestSurface:
    def test_docs_are_not_exposed(self, share_env: ShareEnv) -> None:
        """The share app is public; its route list should not be enumerable."""
        client = share_env["client"]
        assert client.get("/docs").status_code == 404
        assert client.get("/openapi.json").status_code == 404

    def test_main_backend_routes_are_absent(self, share_env: ShareEnv) -> None:
        client = share_env["client"]
        for path in ("/health", "/albums/", "/images/", "/shutdown"):
            assert client.get(path).status_code == 404


def _serve_png_as_img1(share_env: ShareEnv, cluster_name: str = "Ann Example") -> Path:
    """Point img-1 at a real photo carrying Lightroom XMP plus PictoPy's export."""
    photo = Path(_photo(share_env["tmp_path"], "img-1.png"))
    _export_faces(photo, cluster_name)
    conn = sqlite3.connect(share_env["db_path"])
    conn.execute("UPDATE images SET path = ? WHERE id = 'img-1'", (str(photo),))
    conn.commit()
    conn.close()
    return photo


def _export_faces(photo: Path, cluster_name: str) -> None:
    faces = [FaceRecord(embedding=[0.5] * 128, cluster_name=cluster_name)]
    write_image_metadata(str(photo), PictoPyMetadata(faces=faces))


class TestCaching:
    """Real request/response sequences, as a browser revalidating would send them."""

    def _url(
        self, share_env: ShareEnv, kind: str = "photo", image: str = "img-1"
    ) -> str:
        return f"/s/{share_env['token']}/{kind}/{image}"

    def test_first_response_carries_validators(self, share_env: ShareEnv) -> None:
        photo = _serve_png_as_img1(share_env)
        response = share_env["client"].get(self._url(share_env))
        assert response.status_code == 200
        assert response.headers["cache-control"] == "private, no-cache"
        assert response.headers["etag"].startswith('"')
        assert response.headers["last-modified"] == formatdate(
            photo.stat().st_mtime, usegmt=True
        )
        assert int(response.headers["content-length"]) == len(response.content)
        assert b"Ann Example" not in response.content

    def test_revalidation_is_a_bodiless_304_that_never_opens_the_file(
        self, share_env: ShareEnv, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _serve_png_as_img1(share_env)
        client = share_env["client"]
        first = client.get(self._url(share_env))

        def must_not_stream(path: str) -> None:
            raise AssertionError("a 304 must not read the photo")

        monkeypatch.setattr("app.share.routes.open_without_pictopy", must_not_stream)
        again = client.get(
            self._url(share_env), headers={"If-None-Match": first.headers["etag"]}
        )
        assert again.status_code == 304
        assert again.content == b""
        assert again.headers["etag"] == first.headers["etag"]
        assert again.headers["cache-control"] == "private, no-cache"

    @pytest.mark.parametrize(
        "header", ["{etag}", "W/{etag}", '"other", {etag}', "*"], ids=str
    )
    def test_if_none_match_forms(self, share_env: ShareEnv, header: str) -> None:
        _serve_png_as_img1(share_env)
        client = share_env["client"]
        etag = client.get(self._url(share_env)).headers["etag"]
        response = client.get(
            self._url(share_env), headers={"If-None-Match": header.format(etag=etag)}
        )
        assert response.status_code == 304

    def test_stale_etag_gets_the_full_photo(self, share_env: ShareEnv) -> None:
        _serve_png_as_img1(share_env)
        client = share_env["client"]
        full = client.get(self._url(share_env))
        stale = client.get(self._url(share_env), headers={"If-None-Match": '"old"'})
        assert stale.status_code == 200
        assert stale.content == full.content

    def test_if_modified_since(self, share_env: ShareEnv) -> None:
        _serve_png_as_img1(share_env)
        client = share_env["client"]
        last_modified = client.get(self._url(share_env)).headers["last-modified"]

        def status(headers: Dict[str, str]) -> int:
            return client.get(self._url(share_env), headers=headers).status_code

        assert status({"If-Modified-Since": last_modified}) == 304
        assert status({"If-Modified-Since": formatdate(0, usegmt=True)}) == 200
        assert status({"If-Modified-Since": "not a date"}) == 200
        # If-None-Match takes precedence: a wrong ETag means "send it".
        both = {"If-None-Match": '"old"', "If-Modified-Since": last_modified}
        assert status(both) == 200

    def test_edited_photo_is_downloaded_again(self, share_env: ShareEnv) -> None:
        photo = _serve_png_as_img1(share_env)
        client = share_env["client"]
        first = client.get(self._url(share_env))

        Image.new("RGB", (16, 16), (0, 255, 0)).save(photo)
        again = client.get(
            self._url(share_env), headers={"If-None-Match": first.headers["etag"]}
        )
        assert again.status_code == 200
        assert again.headers["etag"] != first.headers["etag"]
        assert Image.open(io.BytesIO(again.content)).size == (16, 16)

    def test_reexport_keeps_mtime_but_size_change_invalidates(
        self, share_env: ShareEnv
    ) -> None:
        photo = _serve_png_as_img1(share_env)
        client = share_env["client"]
        first = client.get(self._url(share_env))
        mtime = photo.stat().st_mtime_ns

        _export_faces(photo, "A much longer cluster name")
        assert photo.stat().st_mtime_ns == mtime
        again = client.get(
            self._url(share_env), headers={"If-None-Match": first.headers["etag"]}
        )
        assert again.status_code == 200
        # Only PictoPy's (stripped) data changed, so the guest's bytes did not.
        assert again.content == first.content

    def test_same_size_reexport_keeps_etag_because_served_bytes_are_identical(
        self, share_env: ShareEnv
    ) -> None:
        """
        Export keeps mtime, so a same-length edit leaves (mtime, size) alone.
        That is safe only because the guest's bytes really are unchanged.
        """
        photo = _serve_png_as_img1(share_env, "Ann Example")
        client = share_env["client"]
        first = client.get(self._url(share_env))
        on_disk = photo.read_bytes()

        _export_faces(photo, "Bob Example")
        assert photo.read_bytes() != on_disk
        assert len(photo.read_bytes()) == len(on_disk)
        again = client.get(self._url(share_env))
        assert again.headers["etag"] == first.headers["etag"]
        assert again.content == first.content

    def test_revoked_share_gets_404_not_304(self, share_env: ShareEnv) -> None:
        _serve_png_as_img1(share_env)
        client = share_env["client"]
        etags = {
            kind: client.get(self._url(share_env, kind)).headers["etag"]
            for kind in ("photo", "thumb")
        }

        share_registry_revoke(share_env["token"])
        for kind, etag in etags.items():
            response = client.get(
                self._url(share_env, kind), headers={"If-None-Match": etag}
            )
            assert response.status_code == 404

    def test_expired_share_gets_404_not_304(self, share_env: ShareEnv) -> None:
        _serve_png_as_img1(share_env)
        client = share_env["client"]
        etag = client.get(self._url(share_env)).headers["etag"]
        expire(share_env["token"])
        response = client.get(self._url(share_env), headers={"If-None-Match": etag})
        assert response.status_code == 404

    def test_locked_share_gets_404_not_304(self, share_env: ShareEnv) -> None:
        _serve_png_as_img1(share_env)
        etag = share_env["client"].get(self._url(share_env)).headers["etag"]
        entry = share_registry_create("album-1", password=PASSWORD)
        response = share_env["client"].get(
            f"/s/{entry.token}/photo/img-1", headers={"If-None-Match": etag}
        )
        assert response.status_code == 404

    def test_thumbnails_revalidate_the_same_way(self, share_env: ShareEnv) -> None:
        client = share_env["client"]
        first = client.get(self._url(share_env, "thumb"))
        assert first.content == THUMB_BYTES
        assert first.headers["cache-control"] == "private, no-cache"
        again = client.get(
            self._url(share_env, "thumb"),
            headers={"If-None-Match": first.headers["etag"]},
        )
        assert again.status_code == 304

    def test_non_png_photo_is_unchanged_but_revalidates(
        self, share_env: ShareEnv
    ) -> None:
        client = share_env["client"]
        first = client.get(self._url(share_env, image="img-2"))
        assert first.content == JPEG_BYTES
        assert first.headers["cache-control"] == "private, no-cache"
        again = client.get(
            self._url(share_env, image="img-2"),
            headers={"If-None-Match": first.headers["etag"]},
        )
        assert again.status_code == 304

    def test_new_strip_rules_invalidate_cached_copies(
        self, share_env: ShareEnv, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _serve_png_as_img1(share_env)
        client = share_env["client"]
        before = client.get(self._url(share_env)).headers["etag"]
        monkeypatch.setattr("app.share.routes._PHOTO_VARIANT", "photo-v2")
        assert client.get(self._url(share_env)).headers["etag"] != before

    def test_validators_describe_the_bytes_actually_streamed(
        self, share_env: ShareEnv, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The file changes between the 304 check and opening it for streaming."""
        photo = _serve_png_as_img1(share_env)
        client = share_env["client"]
        before = client.get(self._url(share_env)).headers["etag"]

        import app.share.routes as routes

        real_open = routes.open_without_pictopy

        def edited_just_before_open(path: str):  # type: ignore[no-untyped-def]
            Image.new("RGB", (16, 16), (0, 0, 255)).save(photo)
            return real_open(path)

        monkeypatch.setattr(routes, "open_without_pictopy", edited_just_before_open)
        raced = client.get(self._url(share_env))
        monkeypatch.setattr(routes, "open_without_pictopy", real_open)

        assert Image.open(io.BytesIO(raced.content)).size == (16, 16)
        assert raced.headers["etag"] != before
        assert raced.headers["etag"] == client.get(self._url(share_env)).headers["etag"]
