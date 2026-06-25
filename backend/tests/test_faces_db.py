import pytest
import sqlite3
import json
import numpy as np
from unittest.mock import patch, MagicMock
from app.database.faces import (
    db_create_faces_table,
    db_insert_face_embeddings,
    db_get_faces_unassigned_clusters,
    db_get_all_faces_with_cluster_names,
    db_update_face_cluster_ids_batch,
    db_get_cluster_mean_embeddings,
)


class TestDbCreateFacesTable:
    # Tests that faces table is created successfully without errors
    def test_create_faces_table_success(self):
        with patch("app.database.faces.sqlite3.connect") as mock_connect:
            mock_conn = MagicMock()
            mock_connect.return_value = mock_conn
            db_create_faces_table()
            mock_conn.cursor.return_value.execute.assert_called_once()
            mock_conn.commit.assert_called_once()

    # Tests that connection is closed even when table creation fails
    def test_create_faces_table_closes_connection_on_error(self):
        with patch("app.database.faces.sqlite3.connect") as mock_connect:
            mock_conn = MagicMock()
            mock_conn.cursor.return_value.execute.side_effect = sqlite3.Error("fail")
            mock_connect.return_value = mock_conn
            with pytest.raises(sqlite3.Error):
                db_create_faces_table()
            mock_conn.close.assert_called_once()


class TestDbInsertFaceEmbeddings:
    # Tests that face embedding is inserted and returns a valid face_id
    def test_insert_face_embeddings_success(self):
        image_id = "test-image-uuid"
        embeddings = [np.array([0.1, 0.2, 0.3])]
        with patch("app.database.faces.sqlite3.connect") as mock_connect:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.lastrowid = 1
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn
            result = db_insert_face_embeddings(image_id, embeddings)
            assert result == 1
            mock_cursor.execute.assert_called_once()
            mock_conn.commit.assert_called_once()

    # Tests that face embedding is inserted with optional confidence and bbox
    def test_insert_face_embeddings_with_metadata(self):
        image_id = "test-image-uuid"
        embeddings = [np.array([0.4, 0.5, 0.6])]
        bbox = {"x": 10, "y": 20, "width": 50, "height": 60}
        with patch("app.database.faces.sqlite3.connect") as mock_connect:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.lastrowid = 2
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn
            result = db_insert_face_embeddings(
                image_id, embeddings, confidence=0.98, bbox=bbox
            )
            assert result == 2
            call_args = mock_cursor.execute.call_args[0][1]
            assert call_args[3] == 0.98
            assert json.loads(call_args[4]) == bbox

    # Tests that connection is always closed after insert
    def test_insert_face_embeddings_closes_connection(self):
        image_id = "test-image-uuid"
        embeddings = [np.array([0.1, 0.2])]
        with patch("app.database.faces.sqlite3.connect") as mock_connect:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.lastrowid = 3
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn
            db_insert_face_embeddings(image_id, embeddings)
            mock_conn.close.assert_called_once()


class TestDbGetFacesUnassignedClusters:
    # Tests that faces without cluster_id are returned as list of dicts
    def test_get_unassigned_faces_returns_list(self):
        fake_embedding = np.array([0.1, 0.2, 0.3])
        fake_rows = [(1, json.dumps(fake_embedding.tolist()))]
        with patch("app.database.faces.sqlite3.connect") as mock_connect:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = fake_rows
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn
            result = db_get_faces_unassigned_clusters()
            assert len(result) == 1
            assert result[0]["face_id"] == 1
            assert isinstance(result[0]["embeddings"], np.ndarray)

    # Tests that empty list is returned when all faces have clusters assigned
    def test_get_unassigned_faces_empty(self):
        with patch("app.database.faces.sqlite3.connect") as mock_connect:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = []
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn
            result = db_get_faces_unassigned_clusters()
            assert result == []
        mock_conn.close.assert_called_once()

class TestDbGetAllFacesWithClusterNames:
    # Tests that faces are returned with their cluster names
    def test_get_faces_with_cluster_names(self):
        fake_embedding = np.array([0.1, 0.2, 0.3])
        fake_rows = [(1, json.dumps(fake_embedding.tolist()), "Alice")]
        with patch("app.database.faces.sqlite3.connect") as mock_connect:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = fake_rows
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn
            result = db_get_all_faces_with_cluster_names()
            assert len(result) == 1
            assert result[0]["face_id"] == 1
            assert result[0]["cluster_name"] == "Alice"
            assert isinstance(result[0]["embeddings"], np.ndarray)

    # Tests that cluster_name is None for faces not assigned to any cluster
    def test_get_faces_with_no_cluster_name(self):
        fake_embedding = np.array([0.5, 0.6])
        fake_rows = [(2, json.dumps(fake_embedding.tolist()), None)]
        with patch("app.database.faces.sqlite3.connect") as mock_connect:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = fake_rows
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn
            result = db_get_all_faces_with_cluster_names()
            assert result[0]["cluster_name"] is None

    # Tests that empty list is returned when no faces exist in database
    def test_get_faces_empty(self):
        with patch("app.database.faces.sqlite3.connect") as mock_connect:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = []
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn
            result = db_get_all_faces_with_cluster_names()
            assert result == []
        mock_conn.close.assert_called_once()

class TestDbUpdateFaceClusterIdsBatch:
    # Tests that batch update runs without error for valid mapping list
    def test_update_batch_success(self):
        mapping = [{"face_id": 1, "cluster_id": 10}, {"face_id": 2, "cluster_id": 20}]
        with patch("app.database.faces.sqlite3.connect") as mock_connect:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn
            db_update_face_cluster_ids_batch(mapping)
            mock_cursor.executemany.assert_called_once()
            mock_conn.commit.assert_called_once()

    # Tests that empty mapping list returns early without any database calls
    def test_update_batch_empty_mapping(self):
        with patch("app.database.faces.sqlite3.connect") as mock_connect:
            db_update_face_cluster_ids_batch([])
            mock_connect.assert_not_called()

    # Tests that cluster_id can be set to None to unassign a face from cluster
    def test_update_batch_with_none_cluster(self):
        mapping = [{"face_id": 1, "cluster_id": None}]
        with patch("app.database.faces.sqlite3.connect") as mock_connect:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn
            db_update_face_cluster_ids_batch(mapping)
            call_args = mock_cursor.executemany.call_args[0][1]
            assert call_args[0] == (None, 1)
        mock_conn.close.assert_called_once()

class TestDbGetClusterMeanEmbeddings:
    # Tests that mean embeddings are calculated correctly per cluster
    def test_get_cluster_mean_embeddings_success(self):
        emb1 = np.array([0.2, 0.4])
        emb2 = np.array([0.6, 0.8])
        fake_rows = [
            (1, json.dumps(emb1.tolist())),
            (1, json.dumps(emb2.tolist())),
        ]
        with patch("app.database.faces.sqlite3.connect") as mock_connect:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = fake_rows
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn
            result = db_get_cluster_mean_embeddings()
            assert len(result) == 1
            assert result[0]["cluster_id"] == 1
            expected_mean = np.mean([emb1, emb2], axis=0)
            np.testing.assert_array_almost_equal(
                result[0]["mean_embedding"], expected_mean
            )

    # Tests that empty list is returned when no faces have cluster assigned
    def test_get_cluster_mean_embeddings_empty(self):
        with patch("app.database.faces.sqlite3.connect") as mock_connect:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = []
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn
            result = db_get_cluster_mean_embeddings()
            assert result == []
            mock_conn.close.assert_called_once()