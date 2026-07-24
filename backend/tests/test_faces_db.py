import json
import os
import sqlite3
import tempfile
from typing import Iterator, Optional

import numpy as np
import pytest

from app.database.faces import (
    db_create_faces_table,
    db_insert_face_embeddings,
    db_get_faces_unassigned_clusters,
    db_get_all_faces_with_cluster_names,
    db_update_face_cluster_ids_batch,
    db_get_cluster_mean_embeddings,
)
from app.database.face_clusters import db_create_clusters_table

# ##############################
# Pytest Fixtures
# ##############################


@pytest.fixture(scope="function")
def test_db(monkeypatch: pytest.MonkeyPatch) -> Iterator[str]:
    """Point the face DB modules at a fresh tempfile database."""
    db_fd, db_path = tempfile.mkstemp()
    os.close(db_fd)

    monkeypatch.setattr("app.config.settings.DATABASE_PATH", db_path)
    monkeypatch.setattr("app.database.faces.DATABASE_PATH", db_path)
    monkeypatch.setattr("app.database.face_clusters.DATABASE_PATH", db_path)

    # clusters first: db_get_all_faces_with_cluster_names LEFT JOINs it
    db_create_clusters_table()
    db_create_faces_table()

    yield db_path

    os.unlink(db_path)


def add_cluster(db_path: str, cluster_id: str, name: str) -> str:
    """Insert a face_clusters row and return its id."""
    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT INTO face_clusters (cluster_id, cluster_name) VALUES (?, ?)",
        (cluster_id, name),
    )
    conn.commit()
    conn.close()
    return cluster_id


def add_face(
    image_id: str = "img-1",
    embedding: Optional[np.ndarray] = None,
    cluster_id: Optional[str] = None,
    **kwargs,
) -> int:
    """Insert a face row and return its generated face_id."""
    if embedding is None:
        embedding = np.array([0.1, 0.2])
    return db_insert_face_embeddings(
        image_id, embedding, cluster_id=cluster_id, **kwargs
    )


# ##############################
# Table creation
# ##############################


class TestFacesTable:
    def test_creates_faces_table(self, test_db):
        conn = sqlite3.connect(test_db)
        tables = {
            row[0]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        conn.close()
        assert "faces" in tables

    def test_is_idempotent(self, test_db):
        # Re-running against an existing schema must not raise
        db_create_faces_table()


# ##############################
# Inserting embeddings
# ##############################


class TestInsertFaceEmbeddings:
    def test_returns_incrementing_face_ids(self, test_db):
        assert add_face("img-1") == 1
        assert add_face("img-2") == 2

    def test_stores_confidence_and_bbox(self, test_db):
        bbox = {"x": 10, "y": 20, "width": 50, "height": 60}
        face_id = add_face("img-1", confidence=0.98, bbox=bbox)

        conn = sqlite3.connect(test_db)
        confidence, bbox_json = conn.execute(
            "SELECT confidence, bbox FROM faces WHERE face_id = ?", (face_id,)
        ).fetchone()
        conn.close()
        assert confidence == 0.98
        assert json.loads(bbox_json) == bbox

    def test_bbox_is_null_when_omitted(self, test_db):
        face_id = add_face("img-1")

        conn = sqlite3.connect(test_db)
        confidence, bbox_json = conn.execute(
            "SELECT confidence, bbox FROM faces WHERE face_id = ?", (face_id,)
        ).fetchone()
        conn.close()
        assert confidence is None
        assert bbox_json is None


# ##############################
# Reading faces
# ##############################


class TestUnassignedFaces:
    def test_lists_only_faces_without_a_cluster(self, test_db):
        cluster = add_cluster(test_db, "cluster-1", "Alice")
        unassigned = add_face("img-1", np.array([0.1, 0.2]))
        add_face("img-2", np.array([0.3, 0.4]), cluster_id=cluster)

        faces = db_get_faces_unassigned_clusters()
        assert [face["face_id"] for face in faces] == [unassigned]
        assert np.allclose(faces[0]["embeddings"], [0.1, 0.2])

    def test_returns_empty_when_all_assigned(self, test_db):
        cluster = add_cluster(test_db, "cluster-1", "Alice")
        add_face("img-1", cluster_id=cluster)
        assert db_get_faces_unassigned_clusters() == []


class TestFacesWithClusterNames:
    def test_returns_the_cluster_name(self, test_db):
        cluster = add_cluster(test_db, "cluster-1", "Alice")
        add_face("img-1", np.array([0.1, 0.2]), cluster_id=cluster)

        faces = db_get_all_faces_with_cluster_names()
        assert len(faces) == 1
        assert faces[0]["cluster_name"] == "Alice"
        assert np.allclose(faces[0]["embeddings"], [0.1, 0.2])

    def test_cluster_name_is_none_when_unassigned(self, test_db):
        add_face("img-1")
        assert db_get_all_faces_with_cluster_names()[0]["cluster_name"] is None

    def test_returns_empty_without_faces(self, test_db):
        assert db_get_all_faces_with_cluster_names() == []


# ##############################
# Cluster assignment
# ##############################


class TestUpdateClusterIdsBatch:
    def test_assigns_clusters_to_faces(self, test_db):
        cluster = add_cluster(test_db, "cluster-1", "Alice")
        first, second = add_face("img-1"), add_face("img-2")

        db_update_face_cluster_ids_batch(
            [
                {"face_id": first, "cluster_id": cluster},
                {"face_id": second, "cluster_id": cluster},
            ]
        )

        assert db_get_faces_unassigned_clusters() == []

    def test_empty_mapping_is_a_noop(self, test_db):
        add_face("img-1")
        db_update_face_cluster_ids_batch([])
        assert len(db_get_faces_unassigned_clusters()) == 1

    def test_none_cluster_unassigns_a_face(self, test_db):
        cluster = add_cluster(test_db, "cluster-1", "Alice")
        face_id = add_face("img-1", cluster_id=cluster)

        db_update_face_cluster_ids_batch([{"face_id": face_id, "cluster_id": None}])

        assert [f["face_id"] for f in db_get_faces_unassigned_clusters()] == [face_id]


# ##############################
# Cluster mean embeddings
# ##############################


class TestClusterMeanEmbeddings:
    def test_averages_embeddings_per_cluster(self, test_db):
        cluster = add_cluster(test_db, "cluster-1", "Alice")
        add_face("img-1", np.array([0.2, 0.4]), cluster_id=cluster)
        add_face("img-2", np.array([0.6, 0.8]), cluster_id=cluster)

        means = db_get_cluster_mean_embeddings()
        assert len(means) == 1
        assert means[0]["cluster_id"] == cluster
        assert np.allclose(means[0]["mean_embedding"], [0.4, 0.6])

    def test_keeps_clusters_separate(self, test_db):
        first = add_cluster(test_db, "cluster-1", "Alice")
        second = add_cluster(test_db, "cluster-2", "Bob")
        add_face("img-1", np.array([0.2, 0.4]), cluster_id=first)
        add_face("img-2", np.array([1.0, 1.0]), cluster_id=second)

        means = {
            row["cluster_id"]: row["mean_embedding"]
            for row in db_get_cluster_mean_embeddings()
        }
        assert np.allclose(means[first], [0.2, 0.4])
        assert np.allclose(means[second], [1.0, 1.0])

    def test_returns_empty_without_assigned_faces(self, test_db):
        add_face("img-1")  # unassigned faces are excluded
        assert db_get_cluster_mean_embeddings() == []
