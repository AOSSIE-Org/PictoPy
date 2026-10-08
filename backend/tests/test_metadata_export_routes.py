"""
The Settings export endpoints, and every edit route that must schedule an
export. Real routers, real database writes, a real (thread) executor.
"""

import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Iterator

import numpy as np
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from PIL import Image

import app.routes.metadata_export as metadata_export_routes
from app.database.albums import db_create_album_with_images
from app.database.face_clusters import db_insert_clusters_batch
from app.database.faces import db_insert_face_embeddings
from app.routes.albums import router as albums_router
from app.routes.face_clusters import router as face_clusters_router
from app.routes.images import router as images_router
from app.routes.metadata_export import router as metadata_export_router
from app.routes.user_preferences import router as user_preferences_router
from app.utils.xmp import read_image_metadata
from tests.test_xmp_exporter import _photo, _tag, make_library
from tests.test_xmp_export_state import db_path as db_path  # noqa: F401 (fixture)


class CountingDebouncer:
    def __init__(self) -> None:
        self.notified = 0

    def notify(self) -> None:
        self.notified += 1


class CountingExecutor(ThreadPoolExecutor):
    def __init__(self) -> None:
        super().__init__(max_workers=1)
        self.submitted = 0

    def submit(self, *args, **kwargs):  # type: ignore[no-untyped-def,override]
        self.submitted += 1
        return super().submit(*args, **kwargs)


@pytest.fixture
def library(db_path: str, tmp_path: Path) -> Path:  # noqa: F811
    return make_library(db_path, tmp_path)


@pytest.fixture
def client(library: Path) -> Iterator[TestClient]:
    app = FastAPI()
    app.include_router(metadata_export_router, prefix="/metadata-export")
    app.include_router(images_router, prefix="/images")
    app.include_router(albums_router, prefix="/albums")
    app.include_router(face_clusters_router, prefix="/face-clusters")
    app.include_router(user_preferences_router, prefix="/user-preferences")
    app.state.executor = CountingExecutor()
    app.state.metadata_export_debouncer = CountingDebouncer()
    with TestClient(app) as test_client:
        yield test_client
    app.state.executor.shutdown(wait=True)


def _state(client: TestClient):  # type: ignore[no-untyped-def]
    return client.app.state  # type: ignore[attr-defined]


def _wait_until_idle(client: TestClient) -> dict:
    for _ in range(200):
        data = client.get("/metadata-export/status").json()["data"]
        if not data["running"]:
            return data
        time.sleep(0.02)
    raise AssertionError("export never finished")


class TestExportEndpoints:
    def test_status_counts_png_images(self, client, library):
        _photo(library, "a")
        _photo(library, "b")
        _photo(library, "j", ext="jpg")
        data = client.get("/metadata-export/status").json()["data"]
        assert (data["total"], data["pending"], data["running"]) == (2, 2, False)
        assert data["last_run"] is None

    def test_run_exports_the_library_and_reports_the_result(self, client, library):
        path = _photo(library, "a")
        _tag("a")
        response = client.post("/metadata-export/run")
        assert response.status_code == 200

        data = _wait_until_idle(client)
        assert data["pending"] == 0
        assert data["last_run"]["written"] == 1
        assert data["run_failed"] is False
        stored = read_image_metadata(path)
        assert stored is not None and stored.tags == ["person"]

    def test_repairs_a_file_another_tool_changed(self, client, library):
        """The button rechecks images already exported, not just pending ones."""
        path = _photo(library, "a")
        _tag("a")
        client.post("/metadata-export/run")
        _wait_until_idle(client)
        Image.open(path).save(path)  # another tool rewrites it, dropping our data
        assert read_image_metadata(path) is None

        client.post("/metadata-export/run")
        assert _wait_until_idle(client)["last_run"]["written"] == 1
        stored = read_image_metadata(path)
        assert stored is not None and stored.tags == ["person"]

    def test_runs_regardless_of_the_automatic_toggle(self, client, library):
        _photo(library, "a")
        _tag("a")  # Metadata_Export was never turned on
        client.post("/metadata-export/run")
        assert _wait_until_idle(client)["last_run"]["written"] == 1

    def test_a_second_click_while_running_starts_nothing(
        self, client, library, monkeypatch
    ):
        release = threading.Event()

        def slow_run(include_clean: bool = False):  # type: ignore[no-untyped-def]
            release.wait(5)
            return {
                "checked": 0,
                "written": 0,
                "unchanged": 0,
                "skipped": 0,
                "failed": 0,
            }

        monkeypatch.setattr(metadata_export_routes, "xmp_export_run", slow_run)
        first = client.post("/metadata-export/run").json()["data"]
        second = client.post("/metadata-export/run").json()["data"]
        assert first["running"] and second["running"]
        assert _state(client).executor.submitted == 1
        release.set()
        assert _wait_until_idle(client)["running"] is False

    def test_a_crashed_run_is_reported(self, client, library, monkeypatch):
        def broken_run(include_clean: bool = False):  # type: ignore[no-untyped-def]
            raise RuntimeError("worker died")

        monkeypatch.setattr(metadata_export_routes, "xmp_export_run", broken_run)
        client.post("/metadata-export/run")
        data = _wait_until_idle(client)
        assert data["run_failed"] is True
        assert data["last_run"] is None


class TestEditsScheduleAnExport:
    """Each edit that changes exported data notifies the debouncer once."""

    def _notified(self, client: TestClient) -> int:
        return _state(client).metadata_export_debouncer.notified

    def _expect(self, client, method: str, url: str, count: int, **kwargs):  # type: ignore[no-untyped-def]
        before = self._notified(client)
        response = client.request(method, url, **kwargs)
        assert self._notified(client) - before == count, (url, response.json())
        return response

    def test_favourite(self, client, library):
        _photo(library, "a")
        r = self._expect(
            client, "POST", "/images/toggle-favourite", 1, json={"image_id": "a"}
        )
        assert r.status_code == 200
        self._expect(
            client, "POST", "/images/toggle-favourite", 0, json={"image_id": "nope"}
        )

    def test_album_edits(self, client, library):
        for i in ("a", "b"):
            _photo(library, i)
        db_create_album_with_images("al", "Trip", "", [])
        self._expect(
            client, "POST", "/albums/al/images", 1, json={"image_ids": ["a", "b"]}
        )
        self._expect(client, "DELETE", "/albums/al/images/a", 1)
        self._expect(
            client, "DELETE", "/albums/al/images", 1, json={"image_ids": ["b"]}
        )
        self._expect(
            client, "PUT", "/albums/al", 1,
            json={"name": "Goa", "description": "", "is_locked": False},
        )  # fmt: skip
        self._expect(client, "DELETE", "/albums/al", 1)
        self._expect(client, "DELETE", "/albums/missing", 0)

    def test_album_from_memory_is_not_exercised_without_a_memory(self, client, library):
        self._expect(
            client, "POST", "/albums/from-memory", 0, json={"memory_id": "nope", "name": "X"}
        )  # fmt: skip

    def test_person_rename_and_recluster(self, client, library, monkeypatch):
        _photo(library, "a")
        db_insert_clusters_batch(
            [{"cluster_id": "c1", "cluster_name": "Ann", "face_image_base64": None}]
        )
        db_insert_face_embeddings("a", np.full(4, 0.5, np.float32), cluster_id="c1")
        monkeypatch.setattr(
            "app.routes.face_clusters._rescore_memories_for_cluster", lambda *a: None
        )
        self._expect(
            client, "PUT", "/face-clusters/c1", 1, json={"cluster_name": "Annabel"}
        )
        self._expect(
            client, "PUT", "/face-clusters/missing", 0, json={"cluster_name": "X"}
        )

        monkeypatch.setattr(
            "app.routes.face_clusters.cluster_util_face_clusters_sync",
            lambda force_full_reclustering=False: (0, 0),
        )
        self._expect(client, "POST", "/face-clusters/global-recluster", 1)

    def test_turning_the_toggle_on_catches_up_the_library(self, client, library):
        self._expect(
            client, "PUT", "/user-preferences/", 1, json={"Metadata_Export": True}
        )
        self._expect(
            client, "PUT", "/user-preferences/", 0, json={"Metadata_Export": False}
        )
        self._expect(
            client, "PUT", "/user-preferences/", 0, json={"GPU_Acceleration": True}
        )

    def test_reads_schedule_nothing(self, client, library):
        _photo(library, "a")
        for url in ("/images/", "/albums/", "/face-clusters/", "/user-preferences/"):
            self._expect(client, "GET", url, 0)

    def test_a_broken_debouncer_never_fails_the_edit(self, client, library):
        _photo(library, "a")

        class Broken:
            def notify(self) -> None:
                raise RuntimeError("boom")

        _state(client).metadata_export_debouncer = Broken()
        response = client.post("/images/toggle-favourite", json={"image_id": "a"})
        assert response.status_code == 200


def test_preference_round_trips(client: TestClient) -> None:
    assert (
        client.get("/user-preferences/").json()["user_preferences"]["Metadata_Export"]
        is False
    )
    body = client.put("/user-preferences/", json={"Metadata_Export": True}).json()
    assert body["user_preferences"]["Metadata_Export"] is True
    assert (
        client.get("/user-preferences/").json()["user_preferences"]["Metadata_Export"]
        is True
    )
