"""
Unit tests for the manual cluster management system.

All database calls are mocked so the tests run in isolation without a
real SQLite database.
"""

import sys
import os
import uuid
from datetime import datetime, timezone
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.routes import manual_clusters as mc_router

# ---------------------------------------------------------------------------
# Test app
# ---------------------------------------------------------------------------

app = FastAPI()
app.include_router(mc_router.router, prefix="/clusters", tags=["Manual Clusters"])
client = TestClient(app)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_NOW = datetime.now(timezone.utc).isoformat()


def _cluster(
    cluster_id: str | None = None,
    name: str = "Test Cluster",
    image_count: int = 0,
) -> dict:
    return {
        "cluster_id": cluster_id or str(uuid.uuid4()),
        "name": name,
        "created_at": _NOW,
        "updated_at": _NOW,
        "is_auto_generated": False,
        "image_count": image_count,
    }


# ---------------------------------------------------------------------------
# POST /clusters/  – Create
# ---------------------------------------------------------------------------


class TestCreateCluster:
    def test_create_cluster_success(self):
        record = _cluster(name="Vacation 2024")
        with patch(
            "app.routes.manual_clusters.create_cluster", return_value=record
        ) as mock_create:
            response = client.post("/clusters/", json={"name": "Vacation 2024"})

        assert response.status_code == 201
        body = response.json()
        assert body["success"] is True
        assert body["data"]["name"] == "Vacation 2024"
        mock_create.assert_called_once_with("Vacation 2024")

    def test_create_cluster_blank_name_rejected(self):
        response = client.post("/clusters/", json={"name": "   "})
        assert response.status_code == 422  # Pydantic validator fires

    def test_create_cluster_empty_name_rejected(self):
        response = client.post("/clusters/", json={"name": ""})
        assert response.status_code == 422

    def test_create_cluster_missing_name_rejected(self):
        response = client.post("/clusters/", json={})
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /clusters/  – List
# ---------------------------------------------------------------------------


class TestListClusters:
    def test_list_clusters_returns_all(self):
        clusters = [_cluster(name="A"), _cluster(name="B")]
        with patch("app.routes.manual_clusters.list_clusters", return_value=clusters):
            response = client.get("/clusters/")

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert len(body["data"]) == 2

    def test_list_clusters_empty(self):
        with patch("app.routes.manual_clusters.list_clusters", return_value=[]):
            response = client.get("/clusters/")

        assert response.status_code == 200
        assert response.json()["data"] == []


# ---------------------------------------------------------------------------
# GET /clusters/{cluster_id}  – Detail
# ---------------------------------------------------------------------------


class TestGetCluster:
    def test_get_existing_cluster(self):
        cid = str(uuid.uuid4())
        detail = {
            "cluster": _cluster(cluster_id=cid, name="Details"),
            "images": [],
            "image_count": 0,
        }
        with patch("app.routes.manual_clusters.get_cluster", return_value=detail):
            response = client.get(f"/clusters/{cid}")

        assert response.status_code == 200
        assert response.json()["data"]["cluster"]["cluster_id"] == cid

    def test_get_missing_cluster_returns_404(self):
        from app.utils.manual_cluster_service import ClusterNotFoundError

        with patch(
            "app.routes.manual_clusters.get_cluster",
            side_effect=ClusterNotFoundError("missing-id"),
        ):
            response = client.get("/clusters/missing-id")

        assert response.status_code == 404


# ---------------------------------------------------------------------------
# PATCH /clusters/{cluster_id}  – Rename
# ---------------------------------------------------------------------------


class TestRenameCluster:
    def test_rename_success(self):
        cid = str(uuid.uuid4())
        updated = _cluster(cluster_id=cid, name="New Name")
        with patch("app.routes.manual_clusters.rename_cluster", return_value=updated):
            response = client.patch(f"/clusters/{cid}", json={"name": "New Name"})

        assert response.status_code == 200
        assert response.json()["data"]["name"] == "New Name"

    def test_rename_missing_cluster(self):
        from app.utils.manual_cluster_service import ClusterNotFoundError

        with patch(
            "app.routes.manual_clusters.rename_cluster",
            side_effect=ClusterNotFoundError("x"),
        ):
            response = client.patch("/clusters/x", json={"name": "X"})

        assert response.status_code == 404

    def test_rename_blank_name_rejected(self):
        response = client.patch("/clusters/some-id", json={"name": "   "})
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# DELETE /clusters/{cluster_id}  – Delete cluster
# ---------------------------------------------------------------------------


class TestDeleteCluster:
    def test_delete_existing_cluster(self):
        cid = str(uuid.uuid4())
        with patch("app.routes.manual_clusters.delete_cluster"):
            response = client.delete(f"/clusters/{cid}")

        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_delete_missing_cluster(self):
        from app.utils.manual_cluster_service import ClusterNotFoundError

        with patch(
            "app.routes.manual_clusters.delete_cluster",
            side_effect=ClusterNotFoundError("x"),
        ):
            response = client.delete("/clusters/x")

        assert response.status_code == 404


# ---------------------------------------------------------------------------
# POST /clusters/{cluster_id}/images  – Bulk assign
# ---------------------------------------------------------------------------


class TestAssignImages:
    def test_bulk_assign_success(self):
        cid = str(uuid.uuid4())
        result = {"assigned_count": 3, "skipped_count": 1}
        with patch("app.routes.manual_clusters.assign_images", return_value=result):
            response = client.post(
                f"/clusters/{cid}/images",
                json={"image_ids": ["a", "b", "c", "d"]},
            )

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["assigned_count"] == 3
        assert body["skipped_count"] == 1

    def test_assign_missing_cluster_returns_404(self):
        from app.utils.manual_cluster_service import ClusterNotFoundError

        with patch(
            "app.routes.manual_clusters.assign_images",
            side_effect=ClusterNotFoundError("x"),
        ):
            response = client.post("/clusters/x/images", json={"image_ids": ["img1"]})

        assert response.status_code == 404

    def test_assign_invalid_image_ids_returns_400(self):
        from app.utils.manual_cluster_service import ImageNotFoundError

        cid = str(uuid.uuid4())
        with patch(
            "app.routes.manual_clusters.assign_images",
            side_effect=ImageNotFoundError(["bad-id"]),
        ):
            response = client.post(
                f"/clusters/{cid}/images", json={"image_ids": ["bad-id"]}
            )

        assert response.status_code == 400

    def test_assign_empty_image_ids_rejected(self):
        cid = str(uuid.uuid4())
        response = client.post(f"/clusters/{cid}/images", json={"image_ids": []})
        assert response.status_code == 422

    def test_assign_missing_body_rejected(self):
        cid = str(uuid.uuid4())
        response = client.post(f"/clusters/{cid}/images", json={})
        assert response.status_code == 422

    def test_duplicate_assignment_skipped(self):
        """All images are already assigned; assigned_count should be 0."""
        cid = str(uuid.uuid4())
        result = {"assigned_count": 0, "skipped_count": 2}
        with patch("app.routes.manual_clusters.assign_images", return_value=result):
            response = client.post(
                f"/clusters/{cid}/images",
                json={"image_ids": ["img1", "img2"]},
            )

        assert response.status_code == 200
        assert response.json()["assigned_count"] == 0
        assert response.json()["skipped_count"] == 2


# ---------------------------------------------------------------------------
# DELETE /clusters/{cluster_id}/images/{image_id}  – Remove image
# ---------------------------------------------------------------------------


class TestRemoveImage:
    def test_remove_existing_assignment(self):
        cid = str(uuid.uuid4())
        iid = "img-1"
        with patch("app.routes.manual_clusters.remove_image"):
            response = client.delete(f"/clusters/{cid}/images/{iid}")

        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_remove_from_missing_cluster_returns_404(self):
        from app.utils.manual_cluster_service import ClusterNotFoundError

        with patch(
            "app.routes.manual_clusters.remove_image",
            side_effect=ClusterNotFoundError("x"),
        ):
            response = client.delete("/clusters/x/images/img-1")

        assert response.status_code == 404

    def test_remove_image_not_in_cluster_returns_404(self):
        from app.utils.manual_cluster_service import ImageNotFoundError

        cid = str(uuid.uuid4())
        with patch(
            "app.routes.manual_clusters.remove_image",
            side_effect=ImageNotFoundError(["img-9"]),
        ):
            response = client.delete(f"/clusters/{cid}/images/img-9")

        assert response.status_code == 404
