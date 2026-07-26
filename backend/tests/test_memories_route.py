from datetime import date
from typing import Any, Dict, Iterator
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routes import memories as memories_route
from app.schemas.user_preferences import MemoriesPreferences

# ##############################
# Pytest Fixtures
# ##############################


@pytest.fixture
def client() -> Iterator[TestClient]:
    """Mount only the memories router, with a stubbed executor."""
    app = FastAPI()
    app.include_router(memories_route.router, prefix="/memories")
    # Unlike the other route tests, this one needs app.state.executor: the
    # generate endpoint hands curation off to it.
    app.state.executor = MagicMock()
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def executor(client: TestClient) -> MagicMock:
    return client.app.state.executor


@pytest.fixture(autouse=True)
def stub_preferences() -> Iterator[None]:
    """Default every test to enabled memories with default weights."""
    with patch.object(
        memories_route,
        "memory_curator_get_preferences",
        return_value=MemoriesPreferences(),
    ):
        yield


def make_memory_row(**overrides: Any) -> Dict[str, Any]:
    row: Dict[str, Any] = {
        "memory_id": "mem-1",
        "dedupe_key": "anniv:07-26:2024",
        "event_type": "anniversary",
        "status": "complete",
        "title": "2 years ago today",
        "subtitle": "July 2024",
        "place_label": None,
        "center_lat": None,
        "center_lon": None,
        "surface_date": "2026-07-26",
        "period_start": "2024-07-26T10:00:00",
        "period_end": "2024-07-26T18:00:00",
        "cover_image_id": "img-0",
        "cover_thumbnail_path": "/thumbs/0.jpg",
        "image_count": 3,
        "live_image_count": 3,
        "score": 0.72,
        "signals": None,
        "params_signature": "sig-1",
        "error": None,
        "notified_at": None,
        "viewed_at": None,
        "dismissed": False,
        "created_at": "2026-07-26T08:00:00",
        "updated_at": "2026-07-26T08:00:00",
    }
    row.update(overrides)
    return row


def make_image_row(index: int) -> Dict[str, Any]:
    return {
        "id": f"img-{index}",
        "path": f"/photos/{index}.jpg",
        "thumbnailPath": f"/thumbs/{index}.jpg",
        "captured_at": "2024-07-26 10:00:00",
        "latitude": None,
        "longitude": None,
        "isFavourite": index == 0,
        "sort_order": index,
        "score": 1.0 - index * 0.1,
    }


def make_run(status: str) -> Dict[str, Any]:
    return {
        "run_date": date.today().isoformat(),
        "status": status,
        "params_signature": "sig-1",
        "generated_count": 0,
        "error": None,
        "started_at": "2026-07-26T08:00:00",
        "finished_at": None,
    }


# ##############################
# POST /memories/generate
# ##############################


class TestGenerateMemories:
    def test_queues_a_run_when_none_exists(
        self, client: TestClient, executor: MagicMock
    ):
        with (
            patch.object(memories_route, "db_reap_stale_memory_runs", return_value=0),
            patch.object(memories_route, "db_get_memory_run", return_value=None),
            patch.object(memories_route, "db_start_memory_run", return_value=True),
        ):
            response = client.post("/memories/generate", json={})

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"]["queued"] is True
        assert body["data"]["status"] == "running"
        assert executor.submit.call_count == 1

    def test_does_not_queue_while_a_run_is_in_progress(
        self, client: TestClient, executor: MagicMock
    ):
        with (
            patch.object(memories_route, "db_reap_stale_memory_runs", return_value=0),
            patch.object(
                memories_route, "db_get_memory_run", return_value=make_run("running")
            ),
        ):
            response = client.post("/memories/generate", json={})

        assert response.json()["data"] == {
            "run_date": date.today().isoformat(),
            "status": "running",
            "queued": False,
        }
        assert executor.submit.call_count == 0

    def test_does_not_requeue_a_completed_run(
        self, client: TestClient, executor: MagicMock
    ):
        with (
            patch.object(memories_route, "db_reap_stale_memory_runs", return_value=0),
            patch.object(
                memories_route, "db_get_memory_run", return_value=make_run("complete")
            ),
        ):
            response = client.post("/memories/generate", json={})

        assert response.json()["data"]["queued"] is False
        assert executor.submit.call_count == 0

    def test_force_requeues_a_completed_run(
        self, client: TestClient, executor: MagicMock
    ):
        with (
            patch.object(memories_route, "db_reap_stale_memory_runs", return_value=0),
            patch.object(
                memories_route, "db_get_memory_run", return_value=make_run("complete")
            ),
            patch.object(memories_route, "db_start_memory_run", return_value=True),
        ):
            response = client.post("/memories/generate", json={"force": True})

        assert response.json()["data"]["queued"] is True
        assert executor.submit.call_count == 1

    @pytest.mark.parametrize("status", ["failed", "running"])
    def test_reaping_runs_before_deciding(self, client: TestClient, status: str):
        """A stale run must be reaped first, or generation blocks forever."""
        with (
            patch.object(
                memories_route, "db_reap_stale_memory_runs", return_value=1
            ) as reap,
            patch.object(
                memories_route, "db_get_memory_run", return_value=make_run(status)
            ),
            patch.object(memories_route, "db_start_memory_run", return_value=True),
        ):
            client.post("/memories/generate", json={})

        reap.assert_called_once_with(memories_route.STALE_RUN_MINUTES)

    def test_failed_runs_are_retried(self, client: TestClient, executor: MagicMock):
        with (
            patch.object(memories_route, "db_reap_stale_memory_runs", return_value=0),
            patch.object(
                memories_route, "db_get_memory_run", return_value=make_run("failed")
            ),
            patch.object(memories_route, "db_start_memory_run", return_value=True),
        ):
            response = client.post("/memories/generate", json={})

        assert response.json()["data"]["queued"] is True
        assert executor.submit.call_count == 1

    @pytest.mark.parametrize("reference_date", ["nope", "2026-13-01", "26/07/2026"])
    def test_rejects_a_malformed_reference_date(
        self, client: TestClient, executor: MagicMock, reference_date: str
    ):
        response = client.post(
            "/memories/generate", json={"reference_date": reference_date}
        )

        assert response.status_code == 400
        assert response.json()["detail"]["error"] == "Validation Error"
        assert executor.submit.call_count == 0

    def test_returns_500_when_the_database_fails(self, client: TestClient):
        with patch.object(
            memories_route, "db_reap_stale_memory_runs", side_effect=Exception("boom")
        ):
            response = client.post("/memories/generate", json={})

        assert response.status_code == 500
        detail = response.json()["detail"]
        assert detail["success"] is False
        assert detail["error"] == "Internal server error"


# ##############################
# GET /memories/today
# ##############################


class TestTodayMemory:
    def test_returns_null_rather_than_404_when_nothing_qualifies(
        self, client: TestClient
    ):
        """This endpoint is polled; an empty library is not an error."""
        with patch.object(
            memories_route, "db_get_surfaceable_memory", return_value=None
        ):
            response = client.get("/memories/today")

        assert response.status_code == 200
        assert response.json()["success"] is True
        assert response.json()["data"]["memory"] is None

    def test_returns_the_full_story_payload(self, client: TestClient):
        with (
            patch.object(
                memories_route,
                "db_get_surfaceable_memory",
                return_value=make_memory_row(),
            ),
            patch.object(
                memories_route,
                "db_get_memory_images",
                return_value=[make_image_row(i) for i in range(3)],
            ),
        ):
            response = client.get("/memories/today")

        memory = response.json()["data"]["memory"]
        assert memory["title"] == "2 years ago today"
        assert [image["id"] for image in memory["images"]] == [
            "img-0",
            "img-1",
            "img-2",
        ]

    def test_returns_500_when_the_database_fails(self, client: TestClient):
        with patch.object(
            memories_route, "db_get_surfaceable_memory", side_effect=Exception("boom")
        ):
            assert client.get("/memories/today").status_code == 500


# ##############################
# GET /memories
# ##############################


class TestListMemories:
    def test_returns_cards_without_images(self, client: TestClient):
        with patch.object(
            memories_route,
            "db_list_memories",
            return_value=([make_memory_row()], 1),
        ):
            response = client.get("/memories")

        body = response.json()["data"]
        assert body["total_count"] == 1
        assert "images" not in body["memories"][0]
        assert body["memories"][0]["cover_thumbnail_path"] == "/thumbs/0.jpg"

    def test_forwards_pagination_and_filters(self, client: TestClient):
        with patch.object(
            memories_route, "db_list_memories", return_value=([], 0)
        ) as listed:
            client.get(
                "/memories",
                params={
                    "limit": 5,
                    "offset": 10,
                    "event_type": "semantic_event",
                    "include_viewed": False,
                    "include_dismissed": True,
                },
            )

        listed.assert_called_once_with(
            limit=5,
            offset=10,
            event_type="semantic_event",
            include_viewed=False,
            include_dismissed=True,
        )

    def test_prefers_the_live_image_count(self, client: TestClient):
        """Deleted photos shrink a memory; the card must not overstate it."""
        row = make_memory_row(image_count=10, live_image_count=2)
        with patch.object(memories_route, "db_list_memories", return_value=([row], 1)):
            response = client.get("/memories")

        assert response.json()["data"]["memories"][0]["image_count"] == 2

    @pytest.mark.parametrize("params", [{"limit": 0}, {"limit": 500}, {"offset": -1}])
    def test_rejects_out_of_range_pagination(
        self, client: TestClient, params: Dict[str, int]
    ):
        assert client.get("/memories", params=params).status_code == 422


# ##############################
# GET /memories/{memory_id}
# ##############################


class TestGetMemory:
    def test_returns_the_story(self, client: TestClient):
        with (
            patch.object(
                memories_route, "db_get_memory", return_value=make_memory_row()
            ),
            patch.object(
                memories_route,
                "db_get_memory_images",
                return_value=[make_image_row(0)],
            ),
        ):
            response = client.get("/memories/mem-1")

        assert response.status_code == 200
        assert response.json()["data"]["memory"]["memory_id"] == "mem-1"

    def test_unknown_id_returns_404(self, client: TestClient):
        with patch.object(memories_route, "db_get_memory", return_value=None):
            response = client.get("/memories/missing")

        assert response.status_code == 404
        assert response.json()["detail"]["error"] == "Not Found"

    @pytest.mark.parametrize("path", ["/memories/status", "/memories/today"])
    def test_literal_routes_win_over_the_id_route(self, client: TestClient, path: str):
        """`/status` and `/today` must not be read as memory ids."""
        with (
            patch.object(memories_route, "db_get_memory") as by_id,
            patch.object(
                memories_route, "db_get_surfaceable_memory", return_value=None
            ),
            patch.object(memories_route, "db_reap_stale_memory_runs", return_value=0),
            patch.object(memories_route, "db_get_memory_run", return_value=None),
            patch.object(memories_route, "db_is_indexing_busy", return_value=False),
            patch.object(memories_route, "db_count_unviewed_memories", return_value=0),
        ):
            assert client.get(path).status_code == 200
            by_id.assert_not_called()


# ##############################
# PATCH /memories/{memory_id}
# ##############################


class TestUpdateMemory:
    @pytest.mark.parametrize(
        "payload, expected",
        [
            ({"viewed": True}, {"viewed": True, "dismissed": None, "notified": None}),
            (
                {"dismissed": True},
                {"viewed": None, "dismissed": True, "notified": None},
            ),
            ({"notified": True}, {"viewed": None, "dismissed": None, "notified": True}),
        ],
    )
    def test_forwards_each_flag(
        self, client: TestClient, payload: Dict[str, bool], expected: Dict[str, Any]
    ):
        with (
            patch.object(
                memories_route, "db_get_memory", return_value=make_memory_row()
            ),
            patch.object(memories_route, "db_get_memory_images", return_value=[]),
            patch.object(memories_route, "db_mark_memory", return_value=True) as mark,
        ):
            response = client.patch("/memories/mem-1", json=payload)

        assert response.status_code == 200
        mark.assert_called_once_with("mem-1", **expected)

    def test_empty_payload_returns_400(self, client: TestClient):
        with patch.object(
            memories_route, "db_get_memory", return_value=make_memory_row()
        ):
            response = client.patch("/memories/mem-1", json={})

        assert response.status_code == 400
        assert response.json()["detail"]["error"] == "Validation Error"

    def test_unknown_id_returns_404(self, client: TestClient):
        with patch.object(memories_route, "db_get_memory", return_value=None):
            response = client.patch("/memories/missing", json={"viewed": True})

        assert response.status_code == 404


# ##############################
# DELETE /memories/{memory_id}
# ##############################


class TestDeleteMemory:
    def test_deletes_an_existing_memory(self, client: TestClient):
        with patch.object(memories_route, "db_delete_memory", return_value=True):
            response = client.delete("/memories/mem-1")

        assert response.status_code == 200
        assert response.json()["data"]["memory_id"] == "mem-1"

    def test_unknown_id_returns_404(self, client: TestClient):
        with patch.object(memories_route, "db_delete_memory", return_value=False):
            assert client.delete("/memories/missing").status_code == 404


# ##############################
# GET /memories/status
# ##############################


class TestMemoryStatus:
    @pytest.mark.parametrize("indexing_busy", [True, False])
    def test_reports_the_scheduler_snapshot(
        self, client: TestClient, indexing_busy: bool
    ):
        with (
            patch.object(memories_route, "db_reap_stale_memory_runs", return_value=0),
            patch.object(
                memories_route, "db_get_memory_run", return_value=make_run("complete")
            ),
            patch.object(
                memories_route, "db_is_indexing_busy", return_value=indexing_busy
            ),
            patch.object(memories_route, "db_count_unviewed_memories", return_value=2),
            patch.object(
                memories_route,
                "db_get_surfaceable_memory",
                return_value=make_memory_row(),
            ),
        ):
            response = client.get("/memories/status")

        data = response.json()["data"]
        assert data["run_status"] == "complete"
        assert data["indexing_busy"] is indexing_busy
        assert data["unviewed_count"] == 2
        assert data["latest_memory_id"] == "mem-1"

    def test_reports_null_run_status_before_the_first_run(self, client: TestClient):
        with (
            patch.object(memories_route, "db_reap_stale_memory_runs", return_value=0),
            patch.object(memories_route, "db_get_memory_run", return_value=None),
            patch.object(memories_route, "db_is_indexing_busy", return_value=False),
            patch.object(memories_route, "db_count_unviewed_memories", return_value=0),
            patch.object(
                memories_route, "db_get_surfaceable_memory", return_value=None
            ),
        ):
            data = client.get("/memories/status").json()["data"]

        assert data["run_status"] is None
        assert data["latest_memory_id"] is None

    @pytest.mark.parametrize(
        "enabled, notifications", [(False, True), (True, False), (False, False)]
    )
    def test_reflects_user_preferences(
        self, client: TestClient, enabled: bool, notifications: bool
    ):
        preferences = MemoriesPreferences(
            enabled=enabled, notifications_enabled=notifications
        )
        with (
            patch.object(
                memories_route,
                "memory_curator_get_preferences",
                return_value=preferences,
            ),
            patch.object(memories_route, "db_reap_stale_memory_runs", return_value=0),
            patch.object(memories_route, "db_get_memory_run", return_value=None),
            patch.object(memories_route, "db_is_indexing_busy", return_value=False),
            patch.object(memories_route, "db_count_unviewed_memories", return_value=0),
            patch.object(
                memories_route, "db_get_surfaceable_memory", return_value=None
            ),
        ):
            data = client.get("/memories/status").json()["data"]

        assert data["memories_enabled"] is enabled
        assert data["notifications_enabled"] is notifications
