import sqlite3
import uuid
from typing import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import tempfile
import os
import shutil
from concurrent.futures import Future, ProcessPoolExecutor


from app.routes.folders import router as folders_router

from app.database.folders import (
    db_create_folders_table,
    db_disable_ai_tagging_batch,
    db_enable_ai_tagging_batch,
    db_update_ai_tagging_batch,
    db_get_folder_ids_by_path_prefix,
    db_get_folder_ids_by_paths,
    db_get_all_folder_details,
    db_get_direct_child_folders,
    db_get_folder_path_from_id,
    db_insert_folders_batch,
    db_insert_folder,
    db_get_folder_id_from_path,
    db_delete_folder,
    db_update_parent_ids_for_subtree,
    db_folder_exists,
    db_delete_folders_batch,
    db_get_all_folder_ids,
    db_get_all_folders,
    db_find_parent_folder_id,
)
from app.database.images import db_create_images_table
from app.database.videos import db_create_videos_table
from app.database.yolo_mapping import db_create_YOLO_classes_table

# Pytest Fixtures


@pytest.fixture(scope="function")
def test_db(monkeypatch: pytest.MonkeyPatch) -> Iterator[str]:
    """Point the folder DB modules at a fresh tempfile database."""
    db_fd, db_path = tempfile.mkstemp()
    os.close(db_fd)
    try:
        monkeypatch.setattr("app.config.settings.DATABASE_PATH", db_path)
        monkeypatch.setattr("app.database.folders.DATABASE_PATH", db_path)
        monkeypatch.setattr("app.database.images.DATABASE_PATH", db_path)
        monkeypatch.setattr("app.database.videos.DATABASE_PATH", db_path)
        monkeypatch.setattr("app.database.yolo_mapping.DATABASE_PATH", db_path)

        # The real schema, not a hand-written copy: a divergent CREATE reorders
        # columns and drops ON DELETE CASCADE, and the whole FK chain must resolve.
        db_create_YOLO_classes_table()
        db_create_folders_table()
        db_create_images_table()  # db_get_all_folder_details LEFT JOINs it
        db_create_videos_table()  # db_get_all_folder_details LEFT JOINs it too

        yield db_path
    finally:
        os.unlink(db_path)


@pytest.fixture
def temp_folder_structure():
    """Create a temporary folder structure for testing."""
    temp_dir = tempfile.mkdtemp()

    folders = {
        "root": temp_dir,
        "photos": os.path.join(temp_dir, "photos"),
        "photos_2023": os.path.join(temp_dir, "photos", "2023"),
        "photos_2024": os.path.join(temp_dir, "photos", "2024"),
        "documents": os.path.join(temp_dir, "documents"),
    }

    for folder_path in folders.values():
        if folder_path != temp_dir:  # root already exists
            os.makedirs(folder_path, exist_ok=True)

    for folder_path in folders.values():
        dummy_file = os.path.join(folder_path, "dummy.txt")
        with open(dummy_file, "w") as f:
            f.write("test content")

    yield folders

    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def app_with_state(test_db):
    """Create FastAPI app instance with mocked state for testing."""
    app = FastAPI()
    app.include_router(folders_router, prefix="/folders")

    app.state.executor = MagicMock(spec=ProcessPoolExecutor)
    app.state.indexing_executor = MagicMock(spec=ProcessPoolExecutor)

    return app


@pytest.fixture
def client(app_with_state):
    """Create test client."""
    return TestClient(app_with_state)


@pytest.fixture
def sample_add_folder_request():
    """Sample add folder request data."""
    return {
        "folder_path": "/test/folder/path",
        "parent_folder_id": None,
        "taggingCompleted": False,
    }


@pytest.fixture
def sample_folder_details():
    """Sample folder details data."""
    return [
        (
            "folder-id-1",
            "/home/user/photos",
            None,
            1693526400,  # timestamp
            True,  # AI_Tagging
            False,  # taggingCompleted
            "completed",  # indexing_status
            0,  # image_count
            7,  # video_count -- a video-only folder is not "empty"
        ),
        (
            "folder-id-2",
            "/home/user/documents",
            None,
            1693526500,
            False,
            True,
            "completed",
            25,
            0,
        ),
    ]


# Test Classes


class TestFoldersAPI:
    """Test class for Folders API endpoints."""

    # POST /folders/add-folder - Add Folder Tests

    @patch("app.routes.folders.folder_util_add_folder_tree")
    @patch("app.routes.folders.db_update_parent_ids_for_subtree")
    @patch("app.routes.folders.db_find_parent_folder_id")
    @patch("app.routes.folders.db_folder_exists")
    def test_add_folder_success(
        self,
        mock_folder_exists,
        mock_find_parent,
        mock_update_parent_ids,
        mock_add_folder_tree,
        client,
        temp_folder_structure,
    ):
        """Test successfully adding a folder."""
        mock_folder_exists.return_value = False
        mock_find_parent.return_value = None
        mock_add_folder_tree.return_value = ("test-folder-id-123", {})
        mock_update_parent_ids.return_value = None

        folder_path = temp_folder_structure["photos"]
        request_data = {
            "folder_path": folder_path,
            "parent_folder_id": None,
            "taggingCompleted": False,
        }

        response = client.post("/folders/add-folder", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Successfully added folder tree" in data["message"]
        assert data["data"]["folder_id"] == "test-folder-id-123"
        assert data["data"]["folder_path"] == folder_path

        mock_folder_exists.assert_called_once_with(folder_path)
        mock_add_folder_tree.assert_called_once()

    @patch("app.routes.folders.db_folder_exists")
    def test_add_folder_already_exists(
        self, mock_folder_exists, client, temp_folder_structure
    ):
        """Test adding folder that already exists in database."""
        mock_folder_exists.return_value = True

        folder_path = temp_folder_structure["photos"]
        request_data = {
            "folder_path": folder_path,
            "parent_folder_id": None,
            "taggingCompleted": False,
        }

        response = client.post("/folders/add-folder", json=request_data)

        assert response.status_code == 409
        data = response.json()
        assert data["detail"]["success"] is False
        assert data["detail"]["error"] == "Folder Already Exists"

    def test_add_folder_invalid_path(self, client):
        """Test adding folder with invalid path."""
        request_data = {
            "folder_path": "/this/path/does/not/exist",
            "parent_folder_id": None,
            "taggingCompleted": False,
        }

        response = client.post("/folders/add-folder", json=request_data)

        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["success"] is False
        assert data["detail"]["error"] == "Validation Error"

    @patch("app.routes.folders.os.access")
    def test_add_folder_permission_denied(
        self, mock_access, client, temp_folder_structure
    ):
        """A folder the process cannot read and traverse is rejected with 401."""
        mock_access.return_value = False

        folder_path = temp_folder_structure["photos"]
        request_data = {
            "folder_path": folder_path,
            "parent_folder_id": None,
            "taggingCompleted": False,
        }

        response = client.post("/folders/add-folder", json=request_data)

        assert response.status_code == 401
        data = response.json()
        assert data["detail"]["success"] is False
        assert data["detail"]["error"] == "Permission denied"

        # The mask matters: os.walk needs X_OK, so R_OK alone would admit a
        # readable-but-unsearchable folder and index nothing under it.
        mock_access.assert_called_once_with(folder_path, os.R_OK | os.X_OK)

    @patch("app.routes.folders.folder_util_add_folder_tree")
    @patch("app.routes.folders.db_update_parent_ids_for_subtree")
    @patch("app.routes.folders.db_find_parent_folder_id")
    @patch("app.routes.folders.db_folder_exists")
    def test_add_folder_with_parent_id(
        self,
        mock_folder_exists,
        mock_find_parent,
        mock_update_parent_ids,
        mock_add_folder_tree,
        client,
        temp_folder_structure,
    ):
        """Test adding folder with specified parent_folder_id."""

        mock_folder_exists.return_value = False
        mock_find_parent.return_value = (
            None  # Should not be called when parent_id provided
        )
        mock_add_folder_tree.return_value = ("child-folder-id", {})
        mock_update_parent_ids.return_value = None

        folder_path = temp_folder_structure["photos_2023"]
        request_data = {
            "folder_path": folder_path,
            "parent_folder_id": "parent-folder-id-123",
            "taggingCompleted": True,
        }

        response = client.post("/folders/add-folder", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["folder_id"] == "child-folder-id"

        # Verify parent lookup was not called since parent_id was provided
        mock_find_parent.assert_not_called()

    @patch("app.routes.folders.folder_util_add_folder_tree")
    @patch("app.routes.folders.db_folder_exists")
    def test_add_folder_database_error(
        self, mock_folder_exists, mock_add_folder_tree, client, temp_folder_structure
    ):
        """Test handling database errors during folder addition."""
        mock_folder_exists.return_value = False
        mock_add_folder_tree.side_effect = Exception("Database connection failed")

        folder_path = temp_folder_structure["photos"]
        request_data = {
            "folder_path": folder_path,
            "parent_folder_id": None,
            "taggingCompleted": False,
        }

        response = client.post("/folders/add-folder", json=request_data)

        assert response.status_code == 500
        data = response.json()
        assert data["detail"]["success"] is False
        assert data["detail"]["error"] == "Internal server error"

    def test_add_folder_missing_required_field(self, client):
        """Test adding folder without required folder_path field."""
        request_data = {"parent_folder_id": None, "taggingCompleted": False}

        response = client.post("/folders/add-folder", json=request_data)

        assert response.status_code == 422  # Validation error

    @patch("app.routes.folders.folder_util_add_folder_tree")
    @patch("app.routes.folders.db_update_parent_ids_for_subtree")
    @patch("app.routes.folders.db_find_parent_folder_id")
    @patch("app.routes.folders.db_folder_exists")
    def test_add_folder_background_processing_called(
        self,
        mock_folder_exists,
        mock_find_parent,
        mock_update_parent_ids,
        mock_add_folder_tree,
        client,
        temp_folder_structure,
    ):
        """Test that background processing is triggered after successful folder addition."""

        mock_folder_exists.return_value = False
        mock_find_parent.return_value = None
        mock_add_folder_tree.return_value = ("test-folder-id", {})
        mock_update_parent_ids.return_value = None

        folder_path = temp_folder_structure["photos"]
        request_data = {
            "folder_path": folder_path,
            "parent_folder_id": None,
            "taggingCompleted": False,
        }

        response = client.post("/folders/add-folder", json=request_data)

        assert response.status_code == 200

        # Indexing pool used, AI/misc pool untouched
        # Access the app state through the client
        app_state = client.app.state
        app_state.indexing_executor.submit.assert_called_once()
        app_state.executor.submit.assert_not_called()

    @patch("app.routes.folders.folder_util_add_folder_tree")
    @patch("app.routes.folders.db_update_parent_ids_for_subtree")
    @patch("app.routes.folders.db_find_parent_folder_id")
    @patch("app.routes.folders.db_folder_exists")
    def test_add_folder_queues_tagging_sweep_once_indexing_completes(
        self,
        mock_folder_exists,
        mock_find_parent,
        mock_update_parent_ids,
        mock_add_folder_tree,
        client,
        temp_folder_structure,
    ):
        """A tagging sweep can start and finish before this folder's images
        are indexed (see _queue_post_index_tagging_sweep). Once indexing's
        future resolves, a catch-up sweep must be queued on the AI pool so
        those images don't sit untagged forever."""
        mock_folder_exists.return_value = False
        mock_find_parent.return_value = None
        mock_add_folder_tree.return_value = ("test-folder-id", {})
        mock_update_parent_ids.return_value = None

        app_state = client.app.state
        index_future: Future = Future()
        app_state.indexing_executor.submit.return_value = index_future

        request_data = {
            "folder_path": temp_folder_structure["photos"],
            "parent_folder_id": None,
            "taggingCompleted": False,
        }
        response = client.post("/folders/add-folder", json=request_data)
        assert response.status_code == 200

        # Indexing hasn't finished yet - no sweep queued yet
        app_state.executor.submit.assert_not_called()

        # Indexing finishes -> catch-up sweep must be queued now
        index_future.set_result(True)
        app_state.executor.submit.assert_called_once()

    # POST /folders/enable-ai-tagging - Enable AI Tagging Tests

    @patch("app.routes.folders.db_enable_ai_tagging_batch")
    def test_enable_ai_tagging_success(self, mock_enable_batch, client):
        """Test successfully enabling AI tagging for folders."""
        mock_enable_batch.return_value = 3  # 3 folders updated

        request_data = {"folder_ids": ["folder-1", "folder-2", "folder-3"]}

        response = client.post("/folders/enable-ai-tagging", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Successfully enabled AI tagging for 3 folder(s)" in data["message"]
        assert data["data"]["updated_count"] == 3
        assert data["data"]["folder_ids"] == ["folder-1", "folder-2", "folder-3"]

        mock_enable_batch.assert_called_once_with(["folder-1", "folder-2", "folder-3"])

    @patch("app.routes.folders.db_enable_ai_tagging_batch")
    def test_enable_ai_tagging_single_folder(self, mock_enable_batch, client):
        """Test enabling AI tagging for single folder."""
        mock_enable_batch.return_value = 1

        request_data = {"folder_ids": ["single-folder-id"]}

        response = client.post("/folders/enable-ai-tagging", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["updated_count"] == 1

    def test_enable_ai_tagging_empty_list(self, client):
        """Test enabling AI tagging with empty folder_ids list."""
        request_data = {"folder_ids": []}

        response = client.post("/folders/enable-ai-tagging", json=request_data)

        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["success"] is False
        assert data["detail"]["error"] == "Validation Error"
        assert "No folder IDs provided" in data["detail"]["message"]

    def test_enable_ai_tagging_missing_field(self, client):
        """Test enabling AI tagging without folder_ids field."""
        request_data = {}

        response = client.post("/folders/enable-ai-tagging", json=request_data)

        assert response.status_code == 422  # Validation error

    @patch("app.routes.folders.db_enable_ai_tagging_batch")
    def test_enable_ai_tagging_database_error(self, mock_enable_batch, client):
        """Test handling database errors during AI tagging enable."""
        mock_enable_batch.side_effect = Exception("Database error")

        request_data = {"folder_ids": ["folder-1", "folder-2"]}

        response = client.post("/folders/enable-ai-tagging", json=request_data)

        assert response.status_code == 500
        data = response.json()
        assert data["detail"]["success"] is False
        assert data["detail"]["error"] == "Internal server error"

    @patch("app.routes.folders.db_enable_ai_tagging_batch")
    def test_enable_ai_tagging_background_processing_called(
        self, mock_enable_batch, client
    ):
        """Test that background processing is triggered after enabling AI tagging."""
        mock_enable_batch.return_value = 2

        request_data = {"folder_ids": ["folder-1", "folder-2"]}

        response = client.post("/folders/enable-ai-tagging", json=request_data)

        assert response.status_code == 200

        app_state = client.app.state
        app_state.executor.submit.assert_called_once()

    # POST /folders/disable-ai-tagging - Disable AI Tagging Tests

    @patch("app.routes.folders.db_disable_ai_tagging_batch")
    def test_disable_ai_tagging_success(self, mock_disable_batch, client):
        """Test successfully disabling AI tagging for folders."""
        mock_disable_batch.return_value = 5  # 5 folders updated

        request_data = {
            "folder_ids": ["folder-1", "folder-2", "folder-3", "folder-4", "folder-5"]
        }

        response = client.post("/folders/disable-ai-tagging", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Successfully disabled AI tagging for 5 folder(s)" in data["message"]
        assert data["data"]["updated_count"] == 5
        assert data["data"]["folder_ids"] == [
            "folder-1",
            "folder-2",
            "folder-3",
            "folder-4",
            "folder-5",
        ]

        mock_disable_batch.assert_called_once_with(
            ["folder-1", "folder-2", "folder-3", "folder-4", "folder-5"]
        )

    @patch("app.routes.folders.db_disable_ai_tagging_batch")
    def test_disable_ai_tagging_single_folder(self, mock_disable_batch, client):
        """Test disabling AI tagging for single folder."""
        mock_disable_batch.return_value = 1

        request_data = {"folder_ids": ["single-folder-id"]}

        response = client.post("/folders/disable-ai-tagging", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["updated_count"] == 1

    def test_disable_ai_tagging_empty_list(self, client):
        """Test disabling AI tagging with empty folder_ids list."""
        request_data = {"folder_ids": []}

        response = client.post("/folders/disable-ai-tagging", json=request_data)

        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["success"] is False
        assert data["detail"]["error"] == "Validation Error"
        assert "No folder IDs provided" in data["detail"]["message"]

    def test_disable_ai_tagging_missing_field(self, client):
        """Test disabling AI tagging without folder_ids field."""
        request_data = {}

        response = client.post("/folders/disable-ai-tagging", json=request_data)

        assert response.status_code == 422  # Validation error

    @patch("app.routes.folders.db_disable_ai_tagging_batch")
    def test_disable_ai_tagging_database_error(self, mock_disable_batch, client):
        """Test handling database errors during AI tagging disable."""
        mock_disable_batch.side_effect = Exception("Database connection failed")

        request_data = {"folder_ids": ["folder-1", "folder-2"]}

        response = client.post("/folders/disable-ai-tagging", json=request_data)

        assert response.status_code == 500
        data = response.json()
        assert data["detail"]["success"] is False
        assert data["detail"]["error"] == "Internal server error"

    @patch("app.routes.folders.db_disable_ai_tagging_batch")
    def test_disable_ai_tagging_no_background_processing(
        self, mock_disable_batch, client
    ):
        """Test that no background processing is triggered when disabling AI tagging."""
        mock_disable_batch.return_value = 2

        request_data = {"folder_ids": ["folder-1", "folder-2"]}

        response = client.post("/folders/disable-ai-tagging", json=request_data)

        assert response.status_code == 200

        # Verify NO background processing was triggered (unlike enable)
        app_state = client.app.state
        app_state.executor.submit.assert_not_called()

    # DELETE /folders/delete-folders - Delete Folders Tests

    @patch("app.routes.folders.db_delete_folders_batch")
    def test_delete_folders_success(self, mock_delete_batch, client):
        """Test successfully deleting multiple folders."""
        mock_delete_batch.return_value = 3

        response = client.request(
            "DELETE",
            "/folders/delete-folders",
            content='{"folder_ids": ["folder-1", "folder-2", "folder-3"]}',
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Successfully deleted 3 folder(s)" in data["message"]
        assert data["data"]["deleted_count"] == 3
        assert data["data"]["folder_ids"] == ["folder-1", "folder-2", "folder-3"]

        mock_delete_batch.assert_called_once_with(["folder-1", "folder-2", "folder-3"])

    @patch("app.routes.folders.db_delete_folders_batch")
    def test_delete_folders_single_folder(self, mock_delete_batch, client):
        """Test deleting a single folder."""
        mock_delete_batch.return_value = 1

        response = client.request(
            "DELETE",
            "/folders/delete-folders",
            content='{"folder_ids": ["single-folder-id"]}',
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["deleted_count"] == 1

    def test_delete_folders_empty_list(self, client):
        """Test deleting folders with empty folder_ids list."""
        response = client.request(
            "DELETE",
            "/folders/delete-folders",
            content='{"folder_ids": []}',
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["success"] is False
        assert data["detail"]["error"] == "Validation Error"
        assert "No folder IDs provided" in data["detail"]["message"]

    @patch("app.routes.folders.db_delete_folders_batch")
    def test_delete_folders_database_error(self, mock_delete_batch, client):
        """Test handling database errors during folder deletion."""
        mock_delete_batch.side_effect = Exception("Database connection failed")

        response = client.request(
            "DELETE",
            "/folders/delete-folders",
            content='{"folder_ids": ["folder-1", "folder-2"]}',
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 500
        data = response.json()
        assert data["detail"]["success"] is False
        assert data["detail"]["error"] == "Internal server error"

    # GET /folders/all-folders - Get All Folders Tests

    @patch("app.routes.folders.db_get_all_folder_details")
    def test_get_all_folders_success(
        self, mock_get_all_folders, client, sample_folder_details
    ):
        """Test successfully retrieving all folders."""
        mock_get_all_folders.return_value = sample_folder_details

        response = client.get("/folders/all-folders")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Successfully retrieved 2 folder(s)" in data["message"]
        assert data["data"]["total_count"] == 2
        assert len(data["data"]["folders"]) == 2

        first_folder = data["data"]["folders"][0]
        assert first_folder["folder_id"] == "folder-id-1"
        assert first_folder["folder_path"] == "/home/user/photos"
        assert first_folder["parent_folder_id"] is None
        assert first_folder["AI_Tagging"] is True
        assert first_folder["taggingCompleted"] is False
        # The video-only fixture folder must surface its media counts.
        assert first_folder["image_count"] == 0
        assert first_folder["video_count"] == 7

        mock_get_all_folders.assert_called_once()

    @patch("app.routes.folders.db_get_all_folder_details")
    def test_get_all_folders_empty(self, mock_get_all_folders, client):
        """Test retrieving all folders when none exist."""
        mock_get_all_folders.return_value = []

        response = client.get("/folders/all-folders")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Successfully retrieved 0 folder(s)" in data["message"]
        assert data["data"]["total_count"] == 0
        assert data["data"]["folders"] == []

    @patch("app.routes.folders.db_get_all_folder_details")
    def test_get_all_folders_database_error(self, mock_get_all_folders, client):
        """Test handling database errors during folder retrieval."""
        mock_get_all_folders.side_effect = Exception("Database connection failed")

        response = client.get("/folders/all-folders")

        assert response.status_code == 500
        data = response.json()
        assert data["detail"]["success"] is False
        assert data["detail"]["error"] == "Internal server error"

    # Edge Cases and Error Handling Tests

    def test_add_folder_malformed_json(self, client):
        """Test adding folder with malformed JSON."""
        response = client.post(
            "/folders/add-folder",
            content='{"malformed_json": true}',
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 422

    @patch("app.routes.folders.db_enable_ai_tagging_batch")
    def test_enable_ai_tagging_partial_update(self, mock_enable_batch, client):
        """Test enabling AI tagging when only some folders are updated."""
        mock_enable_batch.return_value = 2

        request_data = {
            "folder_ids": [
                "existing-folder-1",
                "existing-folder-2",
                "non-existent-folder",
            ]
        }

        response = client.post("/folders/enable-ai-tagging", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["updated_count"] == 2

    @patch("app.routes.folders.db_disable_ai_tagging_batch")
    def test_disable_ai_tagging_no_folders_updated(self, mock_disable_batch, client):
        """Test disabling AI tagging when no folders are actually updated."""
        mock_disable_batch.return_value = 0

        request_data = {
            "folder_ids": ["non-existent-folder-1", "non-existent-folder-2"]
        }

        response = client.post("/folders/disable-ai-tagging", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["updated_count"] == 0

    # Unit Tests


class TestFoldersUnit:

    def test_db_insert_folders_batch(self, test_db):

        db_insert_folders_batch(
            [
                ("folder-id-1", "/tmp/photos", None, 1693526400, True, False),
                ("folder-id-2", "/tmp/docs", None, 1693526500, False, True),
            ]
        )

        conn = sqlite3.connect(test_db)
        rows = conn.execute(
            "SELECT folder_id FROM folders ORDER BY folder_id"
        ).fetchall()
        conn.close()

        assert rows == [("folder-id-1",), ("folder-id-2",)]

    @patch("app.database.folders.sqlite3.connect")
    def test_db_insert_folders_batch_error(self, mock_connect, test_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()

        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        mock_cursor.executemany.side_effect = sqlite3.Error(
            "Database connection failed"
        )

        with pytest.raises(sqlite3.Error):
            db_insert_folders_batch(
                [("folder-id-1", "/tmp/photos", None, 1693526400, True, False)]
            )

        mock_conn.rollback.assert_called_once()
        mock_conn.close.assert_called_once()

    def test_db_insert_folder_generates_uuid_when_folder_id_none(
        self, test_db, tmp_path
    ):
        folder = tmp_path / "photos"
        folder.mkdir()
        fake_uuid = uuid.UUID("12345678-1234-5678-1234-567812345678")
        # test_db already patches DATABASE_PATH, so only uuid4 needs stubbing
        with patch("app.database.folders.uuid.uuid4", return_value=fake_uuid):
            result = db_insert_folder(str(folder), folder_id=None)
        assert result == str(fake_uuid)

    def test_db_insert_folder_success(self, test_db, tmp_path):

        folder = tmp_path / "photos"
        folder.mkdir()

        result = db_insert_folder(str(folder), folder_id="folder-id-1")

        assert result == "folder-id-1"
        assert db_folder_exists(str(folder)) is True

    def test_db_insert_folder_existing_returns_existing_id(self, test_db, tmp_path):

        folder = tmp_path / "photos"
        folder.mkdir()

        first_id = db_insert_folder(str(folder), folder_id="folder-id-1")
        second_id = db_insert_folder(str(folder), folder_id="folder-id-2")

        assert first_id == "folder-id-1"
        assert second_id == "folder-id-1"

    def test_db_insert_folder_invalid_directory(self, test_db):

        with pytest.raises(ValueError):
            db_insert_folder("/path/does/not/exist")

    def test_db_get_folder_id_from_path(self, test_db, tmp_path):

        folder = tmp_path / "docs"
        folder.mkdir()

        db_insert_folder(str(folder), folder_id="folder-id-1")

        result = db_get_folder_id_from_path(str(folder))

        assert result == "folder-id-1"

    def test_db_get_folder_path_from_id(self, test_db, tmp_path):

        folder = tmp_path / "docs"
        folder.mkdir()

        db_insert_folder(str(folder), folder_id="folder-id-1")

        result = db_get_folder_path_from_id("folder-id-1")

        assert result == os.path.abspath(str(folder))

    def test_db_get_all_folders(self, test_db):

        db_insert_folders_batch(
            [
                ("folder-id-1", "/tmp/photos", None, 1693526400, True, False),
                ("folder-id-2", "/tmp/docs", None, 1693526500, False, True),
            ]
        )

        result = db_get_all_folders()

        assert set(result) == {"/tmp/photos", "/tmp/docs"}

    def test_db_get_all_folder_ids(self, test_db):

        db_insert_folders_batch(
            [
                ("folder-id-1", "/tmp/photos", None, 1693526400, True, False),
                ("folder-id-2", "/tmp/docs", None, 1693526500, False, True),
            ]
        )

        result = db_get_all_folder_ids()

        assert set(result) == {"folder-id-1", "folder-id-2"}

    @patch("app.database.folders.sqlite3.connect")
    def test_db_delete_folders_batch_error(self, mock_connect, test_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.execute.side_effect = sqlite3.Error("Database connection failed")
        with pytest.raises(sqlite3.Error):
            db_delete_folders_batch(["folder-id-1"])
        mock_conn.rollback.assert_called_once()
        mock_conn.close.assert_called_once()

    def test_db_delete_folders_batch_empty_list(self, test_db):
        result = db_delete_folders_batch([])
        assert result == 0

    def test_db_delete_folders_batch_success(self, test_db):

        db_insert_folders_batch(
            [
                ("folder-id-1", "/tmp/photos", None, 1693526400, True, False),
                ("folder-id-2", "/tmp/docs", None, 1693526500, False, True),
            ]
        )

        result = db_delete_folders_batch(["folder-id-1"])

        assert result == 1
        assert db_get_folder_path_from_id("folder-id-1") is None
        assert db_get_folder_path_from_id("folder-id-2") == "/tmp/docs"

    def test_db_delete_folder_success(self, test_db, tmp_path):

        folder = tmp_path / "photos"
        folder.mkdir()

        db_insert_folder(str(folder), folder_id="folder-id-1")
        db_delete_folder(str(folder))

        assert db_folder_exists(str(folder)) is False

    def test_db_delete_folder_not_exists(self, test_db, tmp_path):

        folder = tmp_path / "missing"
        folder.mkdir()

        with pytest.raises(ValueError):
            db_delete_folder(str(folder))

    def test_db_update_parent_ids_for_subtree(self, test_db):

        db_insert_folders_batch(
            [
                ("root-id", "/tmp/root", None, 1693526400, True, False),
                ("child-id", "/tmp/root/child", None, 1693526500, True, False),
            ]
        )

        db_update_parent_ids_for_subtree(
            "/tmp/root",
            {
                "/tmp/root": ("root-id", None),
                "/tmp/root/child": ("child-id", "root-id"),
            },
        )

        conn = sqlite3.connect(test_db)
        parent_id = conn.execute(
            "SELECT parent_folder_id FROM folders WHERE folder_id = ?",
            ("child-id",),
        ).fetchone()[0]
        conn.close()

        assert parent_id == "root-id"

    def test_db_update_parent_ids_for_subtree_preserves_existing_parent(self, test_db):
        # The update only rewrites rows whose parent_folder_id is still NULL
        db_insert_folders_batch(
            [
                ("root-id", "/tmp/root", None, 1693526400, True, False),
                ("child-id", "/tmp/root/child", "old-parent", 1693526500, True, False),
            ]
        )

        db_update_parent_ids_for_subtree(
            "/tmp/root",
            {"/tmp/root/child": ("child-id", "root-id")},
        )

        conn = sqlite3.connect(test_db)
        try:
            parent_id = conn.execute(
                "SELECT parent_folder_id FROM folders WHERE folder_id = ?",
                ("child-id",),
            ).fetchone()[0]
        finally:
            conn.close()

        assert parent_id == "old-parent"

    def test_db_folder_exists_true_false(self, test_db, tmp_path):

        folder = tmp_path / "photos"
        folder.mkdir()

        db_insert_folder(str(folder), folder_id="folder-id-1")

        assert db_folder_exists(str(folder)) is True
        assert db_folder_exists(str(tmp_path / "missing")) is False

    def test_db_find_parent_folder_id_root_returns_none(self, test_db):
        # Takes test_db even though the root check short-circuits, so a future
        # change can't silently point this at the real user database.
        result = db_find_parent_folder_id("/")
        assert result is None

    def test_db_find_parent_folder_id_found(self, test_db):
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO folders (folder_id, folder_path) VALUES (?, ?)",
            ("parent-id", "/tmp/photos"),
        )
        conn.commit()
        conn.close()
        result = db_find_parent_folder_id("/tmp/photos/2024")
        assert result == "parent-id"

    def test_db_find_parent_folder_id_not_found(self, test_db):
        # The fixture already yields an empty schema; nothing to seed here
        result = db_find_parent_folder_id("/tmp/photos/2024")
        assert result is None

    def test_db_update_ai_tagging_batch(self, test_db):
        conn = sqlite3.connect(test_db)
        conn.execute(
            "INSERT INTO folders (folder_id, folder_path, AI_Tagging) VALUES (?, ?, ?)",
            ("tmp", "/tmp", False),
        )
        conn.commit()
        conn.close()

        assert db_update_ai_tagging_batch(["tmp"], True) == 1

        # rowcount alone can't tell right column/value from wrong: read it back
        conn = sqlite3.connect(test_db)
        try:
            ai_tagging = conn.execute(
                "SELECT AI_Tagging FROM folders WHERE folder_id = ?", ("tmp",)
            ).fetchone()[0]
        finally:
            conn.close()
        assert ai_tagging == 1

    def test_db_update_ai_tagging_batch_empty_list(self, test_db):
        assert db_update_ai_tagging_batch([], True) == 0

    @patch("app.database.folders.sqlite3.connect")
    def test_db_update_ai_tagging_batch_sqlite_error(self, mock_connect, test_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()

        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        mock_cursor.execute.side_effect = sqlite3.Error("fake db error")

        with pytest.raises(sqlite3.Error):
            db_update_ai_tagging_batch(["folder-id-1"], False)

        mock_conn.rollback.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch("app.database.folders.db_update_ai_tagging_batch")
    def test_db_enable_ai_tagging_batch(self, mock_update_batch, test_db):
        mock_update_batch.return_value = 1
        result = db_enable_ai_tagging_batch(["tmp"])
        assert result == 1
        mock_update_batch.assert_called_once_with(["tmp"], True)

    @patch("app.database.folders.db_update_ai_tagging_batch")
    def test_db_disable_ai_tagging_batch(self, mock_update_batch, test_db):
        mock_update_batch.return_value = 1
        result = db_disable_ai_tagging_batch(["tmp"])
        assert result == 1
        mock_update_batch.assert_called_once_with(["tmp"], False)

    def test_db_get_folder_ids_by_path_prefix(self, test_db):
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        cursor.executemany(
            "INSERT INTO folders (folder_id, folder_path) VALUES (?, ?)",
            [
                ("folder-id-1", "/tmp/photos"),
                ("folder-id-2", "/tmp/photos/2024"),
                ("folder-id-3", "/other/documents"),
            ],
        )
        conn.commit()
        conn.close()
        result = db_get_folder_ids_by_path_prefix("/tmp")
        # The query has no ORDER BY, so row order isn't part of the contract
        assert set(result) == {
            ("folder-id-1", "/tmp/photos"),
            ("folder-id-2", "/tmp/photos/2024"),
        }

    def test_db_get_folder_ids_by_paths(self, test_db):
        conn = sqlite3.connect(test_db)
        folder1 = os.path.abspath("test_folder_1")
        folder2 = os.path.abspath("test_folder_2")
        conn.execute(
            "INSERT INTO folders (folder_id, folder_path) VALUES (?, ?)",
            ("id_1", folder1),
        )
        conn.execute(
            "INSERT INTO folders (folder_id, folder_path) VALUES (?, ?)",
            ("id_2", folder2),
        )
        conn.commit()
        conn.close()
        result = db_get_folder_ids_by_paths(
            [
                "test_folder_1",
                "test_folder_2",
            ]
        )
        assert result == {
            folder1: "id_1",
            folder2: "id_2",
        }

    def test_db_get_folder_ids_by_paths_empty(self, test_db):
        result = db_get_folder_ids_by_paths([])
        assert result == {}

    def test_db_get_all_folder_details(self, test_db):
        conn = sqlite3.connect(test_db)
        # Name the columns: a positional INSERT binds to the wrong ones, since
        # parent_folder_id precedes folder_path in the real schema.
        conn.execute(
            """
            INSERT INTO folders (folder_id, folder_path, parent_folder_id,
                                 last_modified_time, AI_Tagging, taggingCompleted)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("folder-id-1", "/home/user/photos", None, 1693526400, True, False),
        )
        conn.executemany(
            "INSERT INTO images (id, path, folder_id) VALUES (?, ?, ?)",
            [
                ("img-1", "/home/user/photos/a.jpg", "folder-id-1"),
                ("img-2", "/home/user/photos/b.jpg", "folder-id-1"),
            ],
        )
        conn.commit()
        conn.close()
        result = db_get_all_folder_details()
        assert result == [
            (
                "folder-id-1",
                "/home/user/photos",
                None,
                1693526400,
                1,  # AI_Tagging
                0,  # taggingCompleted
                "not_started",  # indexing_status (schema default)
                2,  # image_count
                0,  # video_count
            )
        ]

    def test_db_get_all_folder_details_counts_videos(self, test_db):
        """Distinct image/video counts on both sides of the media join.

        The mixed folder deliberately has >1 of each: the images x videos
        join fans out to 2*2=4 rows, so counting anything but DISTINCT ids
        would over-report. A separate video-only folder pins image_count=0.
        """
        conn = sqlite3.connect(test_db)
        conn.executemany(
            """
            INSERT INTO folders (folder_id, folder_path, parent_folder_id,
                                 last_modified_time, AI_Tagging, taggingCompleted)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                ("mixed", "/home/user/media", None, 1693526400, True, False),
                ("videos-only", "/home/user/clips", None, 1693526400, True, False),
            ],
        )
        conn.executemany(
            "INSERT INTO images (id, path, folder_id) VALUES (?, ?, ?)",
            [
                ("img-1", "/home/user/media/a.jpg", "mixed"),
                ("img-2", "/home/user/media/b.jpg", "mixed"),
            ],
        )
        conn.executemany(
            "INSERT INTO videos (id, path, folder_id) VALUES (?, ?, ?)",
            [
                ("vid-1", "/home/user/media/a.mp4", "mixed"),
                ("vid-2", "/home/user/media/b.mp4", "mixed"),
                ("vid-3", "/home/user/clips/c.mp4", "videos-only"),
            ],
        )
        conn.commit()
        conn.close()

        # (image_count, video_count) keyed by folder_id, order-independent.
        counts = {row[0]: (row[7], row[8]) for row in db_get_all_folder_details()}
        assert counts["mixed"] == (2, 2)
        assert counts["videos-only"] == (0, 1)

    def test_db_get_direct_child_folders(self, test_db):
        conn = sqlite3.connect(test_db)
        conn.execute(
            "INSERT INTO folders (folder_id, folder_path, parent_folder_id) VALUES (?, ?, ?)",
            ("root", "/root", None),
        )
        conn.execute(
            "INSERT INTO folders (folder_id, folder_path, parent_folder_id) VALUES (?, ?, ?)",
            ("child_1", "/root/child1", "root"),
        )
        conn.execute(
            "INSERT INTO folders (folder_id, folder_path, parent_folder_id) VALUES (?, ?, ?)",
            ("child_2", "/root/child2", "root"),
        )
        conn.execute(
            "INSERT INTO folders (folder_id, folder_path, parent_folder_id) VALUES (?, ?, ?)",
            ("grandchild", "/root/child1/grandchild", "child_1"),
        )
        conn.commit()
        conn.close()
        result = db_get_direct_child_folders("root")
        assert set(result) == {
            ("child_1", "/root/child1"),
            ("child_2", "/root/child2"),
        }


# Integration & Workflow Tests
class TestFoldersIntegration:
    @patch("app.routes.folders.folder_util_add_folder_tree")
    @patch("app.routes.folders.db_update_parent_ids_for_subtree")
    @patch("app.routes.folders.db_find_parent_folder_id")
    @patch("app.routes.folders.db_folder_exists")
    @patch("app.routes.folders.db_enable_ai_tagging_batch")
    def test_complete_folder_workflow(
        self,
        mock_enable_batch,
        mock_folder_exists,
        mock_find_parent,
        mock_update_parent_ids,
        mock_add_folder_tree,
        client,
        temp_folder_structure,
    ):
        """Test complete folder workflow: add folder -> enable AI tagging."""
        mock_folder_exists.return_value = False
        mock_find_parent.return_value = None
        mock_add_folder_tree.return_value = ("new-folder-id", {})
        mock_update_parent_ids.return_value = None

        mock_enable_batch.return_value = 1

        folder_path = temp_folder_structure["photos"]

        add_request = {
            "folder_path": folder_path,
            "parent_folder_id": None,
            "taggingCompleted": False,
        }

        add_response = client.post("/folders/add-folder", json=add_request)
        assert add_response.status_code == 200
        folder_id = add_response.json()["data"]["folder_id"]

        enable_request = {"folder_ids": [folder_id]}

        enable_response = client.post("/folders/enable-ai-tagging", json=enable_request)
        assert enable_response.status_code == 200
        assert enable_response.json()["data"]["updated_count"] == 1

        mock_add_folder_tree.assert_called_once()
        mock_enable_batch.assert_called_once_with([folder_id])

    @patch("app.routes.folders.db_enable_ai_tagging_batch")
    @patch("app.routes.folders.db_disable_ai_tagging_batch")
    def test_ai_tagging_toggle_workflow(
        self, mock_disable_batch, mock_enable_batch, client
    ):
        """Test toggling AI tagging on and off for folders."""
        folder_ids = ["folder-1", "folder-2"]

        mock_enable_batch.return_value = 2
        mock_disable_batch.return_value = 2

        enable_request = {"folder_ids": folder_ids}
        enable_response = client.post("/folders/enable-ai-tagging", json=enable_request)
        assert enable_response.status_code == 200
        assert enable_response.json()["data"]["updated_count"] == 2

        disable_request = {"folder_ids": folder_ids}
        disable_response = client.post(
            "/folders/disable-ai-tagging", json=disable_request
        )
        assert disable_response.status_code == 200
        assert disable_response.json()["data"]["updated_count"] == 2

        mock_enable_batch.assert_called_once_with(folder_ids)
        mock_disable_batch.assert_called_once_with(folder_ids)

    @patch("app.routes.folders.folder_util_add_folder_tree")
    @patch("app.routes.folders.db_update_parent_ids_for_subtree")
    @patch("app.routes.folders.db_find_parent_folder_id")
    @patch("app.routes.folders.db_folder_exists")
    def test_nested_folder_addition_workflow(
        self,
        mock_folder_exists,
        mock_find_parent,
        mock_update_parent_ids,
        mock_add_folder_tree,
        client,
        temp_folder_structure,
    ):
        """Test adding nested folders with parent-child relationships."""
        mock_folder_exists.return_value = False
        mock_add_folder_tree.return_value = ("folder-id", {})
        mock_update_parent_ids.return_value = None

        def mock_find_parent_side_effect(folder_path):
            if "2023" in folder_path or "2024" in folder_path:
                return "photos-parent-id"
            return None

        mock_find_parent.side_effect = mock_find_parent_side_effect

        parent_request = {
            "folder_path": temp_folder_structure["photos"],
            "parent_folder_id": None,
            "taggingCompleted": False,
        }

        parent_response = client.post("/folders/add-folder", json=parent_request)
        assert parent_response.status_code == 200

        child_request = {
            "folder_path": temp_folder_structure["photos_2023"],
            "parent_folder_id": None,
            "taggingCompleted": False,
        }

        child_response = client.post("/folders/add-folder", json=child_request)
        assert child_response.status_code == 200

        assert mock_find_parent.call_count >= 1

    @patch("app.routes.folders.db_delete_folders_batch")
    @patch("app.routes.folders.db_enable_ai_tagging_batch")
    def test_complete_folder_lifecycle(
        self, mock_enable_batch, mock_delete_batch, client
    ):
        """Test complete folder lifecycle: enable AI -> delete."""
        folder_ids = ["folder-1", "folder-2"]

        # Enable AI tagging
        mock_enable_batch.return_value = 2
        enable_request = {"folder_ids": folder_ids}
        enable_response = client.post("/folders/enable-ai-tagging", json=enable_request)
        assert enable_response.status_code == 200

        mock_delete_batch.return_value = 2
        delete_response = client.request(
            "DELETE",
            "/folders/delete-folders",
            content='{"folder_ids": ["folder-1", "folder-2"]}',
            headers={"Content-Type": "application/json"},
        )
        assert delete_response.status_code == 200
        assert delete_response.json()["data"]["deleted_count"] == 2

        mock_enable_batch.assert_called_once_with(folder_ids)
        mock_delete_batch.assert_called_once_with(folder_ids)
