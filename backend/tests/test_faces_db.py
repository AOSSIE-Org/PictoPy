import json
import os
import sqlite3
import tempfile
from contextlib import closing
from typing import Iterator, Optional
from unittest.mock import MagicMock, patch

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

    def test_closes_the_connection_when_create_fails(self):
        """The finally-based cleanup must still run when the CREATE raises.

        Mocked deliberately: a real CREATE can't be made to fail while leaving
        the connection observable.
        """
        with patch("app.database.faces.sqlite3.connect") as mock_connect:
            conn = MagicMock()
            conn.cursor.return_value.execute.side_effect = sqlite3.Error("fail")
            mock_connect.return_value = conn

            with pytest.raises(sqlite3.Error):
                db_create_faces_table()

            conn.close.assert_called_once()


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

    def test_caller_supplied_cursor_is_left_uncommitted(self, test_db):
        """With a caller's cursor the helper must not commit or close it --
        the caller owns the transaction."""
        cluster = add_cluster(test_db, "cluster-1", "Alice")
        face_id = add_face("img-1")

        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        db_update_face_cluster_ids_batch(
            [{"face_id": face_id, "cluster_id": cluster}], cursor=cursor
        )

        # Visible inside the caller's transaction, and the cursor still works
        assigned = cursor.execute(
            "SELECT cluster_id FROM faces WHERE face_id = ?", (face_id,)
        ).fetchone()
        assert assigned[0] == cluster

        # Nothing was committed, so rolling back discards the update
        conn.rollback()
        conn.close()
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


# ##############################
# Video keyframe faces
# ##############################


def _legacy_faces_schema(db_path: str) -> None:
    """Recreate the pre-frame_id faces table, as a shipped database has it."""
    conn = sqlite3.connect(db_path)
    conn.execute("DROP TABLE IF EXISTS faces")
    conn.execute(
        """
        CREATE TABLE faces (
            face_id INTEGER PRIMARY KEY AUTOINCREMENT,
            image_id TEXT,
            cluster_id INTEGER,
            embeddings TEXT,
            confidence REAL,
            bbox TEXT,
            FOREIGN KEY (image_id) REFERENCES images(id) ON DELETE CASCADE,
            FOREIGN KEY (cluster_id) REFERENCES face_clusters(cluster_id)
                ON DELETE SET NULL
        )
        """
    )
    conn.execute(
        "INSERT INTO faces (image_id, embeddings) VALUES ('legacy-img', '[[0.1]]')"
    )
    conn.commit()
    conn.close()


def _columns(db_path: str, table: str) -> set:
    conn = sqlite3.connect(db_path)
    try:
        return {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
    finally:
        conn.close()


class TestFrameIdColumn:
    def test_fresh_table_has_frame_id(self, test_db):
        assert "frame_id" in _columns(test_db, "faces")

    def test_creates_frame_id_index(self, test_db):
        conn = sqlite3.connect(test_db)
        indexes = {
            row[0]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type='index'")
        }
        conn.close()
        assert "ix_faces_frame_id" in indexes

    def test_migrates_a_legacy_table(self, test_db):
        """A database shipped before frame_id existed gains the column, and its
        rows survive -- CREATE IF NOT EXISTS alone would silently skip it."""
        _legacy_faces_schema(test_db)
        assert "frame_id" not in _columns(test_db, "faces")

        db_create_faces_table()

        assert "frame_id" in _columns(test_db, "faces")
        conn = sqlite3.connect(test_db)
        rows = conn.execute("SELECT image_id, frame_id FROM faces").fetchall()
        conn.close()
        assert rows == [("legacy-img", None)]

    def test_migration_is_idempotent(self, test_db):
        _legacy_faces_schema(test_db)
        db_create_faces_table()
        db_create_faces_table()  # must not raise on the second pass
        assert "frame_id" in _columns(test_db, "faces")


class TestVideoFaces:
    def test_stores_a_face_against_a_keyframe(self, test_db):
        face_id = add_face(image_id=None, frame_id="frame-1")

        conn = sqlite3.connect(test_db)
        image_id, frame_id = conn.execute(
            "SELECT image_id, frame_id FROM faces WHERE face_id = ?", (face_id,)
        ).fetchone()
        conn.close()
        assert image_id is None
        assert frame_id == "frame-1"

    def test_photo_faces_leave_frame_id_null(self, test_db):
        face_id = add_face("img-1")

        conn = sqlite3.connect(test_db)
        (frame_id,) = conn.execute(
            "SELECT frame_id FROM faces WHERE face_id = ?", (face_id,)
        ).fetchone()
        conn.close()
        assert frame_id is None

    def test_rejects_both_ids(self, test_db):
        with pytest.raises(ValueError):
            add_face("img-1", frame_id="frame-1")

    def test_rejects_neither_id(self, test_db):
        with pytest.raises(ValueError):
            add_face(image_id=None)

    def test_unassigned_faces_expose_frame_id(self, test_db):
        add_face(image_id=None, frame_id="frame-1")

        (face,) = db_get_faces_unassigned_clusters()
        assert face["frame_id"] == "frame-1"
        assert face["image_id"] is None

    def test_cluster_name_listing_exposes_frame_id(self, test_db):
        cluster = add_cluster(test_db, "cluster-1", "Alice")
        add_face(image_id=None, frame_id="frame-1", cluster_id=cluster)

        (face,) = db_get_all_faces_with_cluster_names()
        assert face["frame_id"] == "frame-1"
        assert face["cluster_name"] == "Alice"


class TestVideoFaceCascade:
    def test_deleting_a_video_removes_its_frame_faces(self, test_db, monkeypatch):
        """Two-hop cascade: videos -> video_frames -> faces. Photo faces must be
        untouched. The delete needs its own FK-enabled connection because the
        write paths in this module do not enable foreign keys."""
        from app.database import folders as folders_db
        from app.database import images as images_db
        from app.database import videos as videos_db
        from app.database import video_frames as video_frames_db
        from app.database import yolo_mapping as yolo_db

        monkeypatch.setattr(folders_db, "DATABASE_PATH", test_db)
        monkeypatch.setattr(images_db, "DATABASE_PATH", test_db)
        monkeypatch.setattr(videos_db, "DATABASE_PATH", test_db)
        monkeypatch.setattr(yolo_db, "DATABASE_PATH", test_db)

        # Every parent the cascade touches has to exist: with FKs on, SQLite
        # resolves them even for NULL children, and deleting a video walks
        # video_frames and video_classes (which references mappings).
        folders_db.db_create_folders_table()
        yolo_db.db_create_YOLO_classes_table()
        images_db.db_create_images_table()
        videos_db.db_create_videos_table()
        video_frames_db.db_create_video_frames_tables()
        db_create_faces_table()

        with closing(sqlite3.connect(test_db)) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("INSERT INTO images (id, path) VALUES ('img-1', '/a.jpg')")
            conn.execute("INSERT INTO videos (id, path) VALUES ('vid-1', '/a.mp4')")
            conn.execute(
                "INSERT INTO video_frames (id, video_id, frame_path) "
                "VALUES ('frame-1', 'vid-1', '/f.jpg')"
            )
            conn.commit()

        add_face("img-1")
        add_face(image_id=None, frame_id="frame-1")

        with closing(sqlite3.connect(test_db)) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("DELETE FROM videos WHERE id = 'vid-1'")
            conn.commit()
            remaining = conn.execute("SELECT image_id, frame_id FROM faces").fetchall()

        assert remaining == [("img-1", None)]
