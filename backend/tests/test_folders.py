import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import tempfile
import os
import shutil
from concurrent.futures import ProcessPoolExecutor


from app.routes.folders import router as folders_router


# ##############################
# Pytest Fixtures
# ##############################


@pytest.fixture(scope="function")
def test_db():
    """Create a temporary test database for each test."""
    db_fd, db_path = tempfile.mkstemp()

    import app.config.settings

    original_db_path = app.config.settings.DATABASE_PATH
    app.config.settings.DATABASE_PATH = db_path

    yield db_path

    app.config.settings.DATABASE_PATH = original_db_path
    os.close(db_fd)
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

    # Mock the executor state
    app.state.executor = MagicMock(spec=ProcessPoolExecutor)

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
        ),
        (
            "folder-id-2",
            "/home/user/documents",
            None,
            1693526500,
            False,
            True,
        ),
    ]


# ##############################
# Test Classes
# ##############################


class TestFoldersAPI:
    """Test class for Folders API endpoints."""

    # ============================================================================
    # POST /folders/add-folder - Add Folder Tests
    # ============================================================================

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

        # Verify mocks were called correctly
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

    # @patch('app.routes.folders.os.access')
    # def test_add_folder_permission_denied(self, mock_access, client, temp_folder_structure):
    #     """Test adding folder without read permissions."""
    #     mock_access.return_value = False  # Simulate no read permission

    #     folder_path = temp_folder_structure["photos"]
    #     request_data = {
    #         "folder_path": folder_path,
    #         "parent_folder_id": None,
    #         "taggingCompleted": False
    #     }

    #     response = client.post("/folders/add-folder", json=request_data)

    #     assert response.status_code == 401
    #     data = response.json()
    #     assert data["detail"]["success"] is False
    #     assert data["detail"]["error"] == "Permission denied"

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

        # Verify that the executor.submit was called for background processing
        # Access the app state through the client
        app_state = client.app.state
        app_state.executor.submit.assert_called_once()

    # ============================================================================
    # POST /folders/enable-ai-tagging - Enable AI Tagging Tests
    # ============================================================================

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

        # Verify background processing was triggered
        app_state = client.app.state
        app_state.executor.submit.assert_called_once()

    # ============================================================================
    # POST /folders/disable-ai-tagging - Disable AI Tagging Tests
    # ============================================================================

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

    # ============================================================================
    # DELETE /folders/delete-folders - Delete Folders Tests
    # ============================================================================

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

    # ============================================================================
    # GET /folders/all-folders - Get All Folders Tests
    # ============================================================================

    @patch("app.routes.folders.db_get_all_folder_details")
    @patch("app.routes.folders.os.path.isdir")
    def test_get_all_folders_success(
        self, mock_isdir, mock_get_all_folders, client, sample_folder_details
    ):
        """Test successfully retrieving all folders."""
        mock_get_all_folders.return_value = sample_folder_details
        mock_isdir.return_value = True

        response = client.get("/folders/all-folders")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Successfully retrieved 2 folder(s)" in data["message"]
        assert data["data"]["total_count"] == 2
        assert len(data["data"]["folders"]) == 2

        # Check first folder details
        first_folder = data["data"]["folders"][0]
        assert first_folder["folder_id"] == "folder-id-1"
        assert first_folder["folder_path"] == "/home/user/photos"
        assert first_folder["parent_folder_id"] is None
        assert first_folder["AI_Tagging"] is True
        assert first_folder["taggingCompleted"] is False
        assert first_folder["exists"] is True

        mock_get_all_folders.assert_called_once()
        assert mock_isdir.call_count == 2

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

    # ============================================================================
    # Edge Cases and Error Handling Tests
    # ============================================================================

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

    # ============================================================================
    # Integration & Workflow Tests
    # ============================================================================

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

        # Delete folders
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
