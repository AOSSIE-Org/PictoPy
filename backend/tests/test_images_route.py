from typing import Iterator
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routes.images import router as images_router


@pytest.fixture
def client() -> Iterator[TestClient]:
    app = FastAPI()
    app.include_router(images_router, prefix="/images")
    app.state.executor = MagicMock()
    with TestClient(app) as test_client:
        yield test_client


class TestDeleteImagesMemoryMaintenance:
    @patch("app.utils.memory_curator.memory_curator_run")
    @patch("app.utils.memory_curator.memory_curator_prune_empty")
    @patch("app.routes.images.image_util_delete_images")
    def test_prunes_and_queues_curation_after_image_delete(
        self,
        mock_delete: MagicMock,
        mock_prune: MagicMock,
        mock_curate: MagicMock,
        client: TestClient,
    ) -> None:
        mock_delete.return_value = {"deleted_ids": ["image-1"], "failed_paths": []}

        response = client.request(
            "DELETE",
            "/images/delete-images",
            json={"image_ids": ["image-1"]},
        )

        assert response.status_code == 200
        mock_prune.assert_called_once_with()
        client.app.state.executor.submit.assert_called_once_with(
            mock_curate, trigger="image_delete"
        )

    @patch("app.utils.memory_curator.memory_curator_run")
    @patch("app.utils.memory_curator.memory_curator_prune_empty")
    @patch("app.routes.images.image_util_delete_images")
    def test_skips_memory_maintenance_when_no_images_were_deleted(
        self,
        mock_delete: MagicMock,
        mock_prune: MagicMock,
        mock_curate: MagicMock,
        client: TestClient,
    ) -> None:
        mock_delete.return_value = {"deleted_ids": [], "failed_paths": []}

        response = client.request(
            "DELETE",
            "/images/delete-images",
            json={"image_ids": ["missing-image"]},
        )

        assert response.status_code == 200
        mock_prune.assert_not_called()
        mock_curate.assert_not_called()
        client.app.state.executor.submit.assert_not_called()
