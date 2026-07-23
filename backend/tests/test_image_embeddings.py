import numpy as np
import pytest

import app.database.images as images_module
import app.database.folders as folders_module
import app.database.yolo_mapping as yolo_mapping_module
import app.database.connection as connection_module
from app.database.images import _connect, db_create_images_table
from app.database.connection import get_db_connection
from app.database.folders import db_create_folders_table
from app.database.yolo_mapping import db_create_YOLO_classes_table
from app.database.image_embeddings import (
    db_create_image_embeddings_table,
    db_upsert_image_embeddings,
    db_get_all_embeddings,
    db_count_embeddings,
)


@pytest.fixture(autouse=True)
def _isolated_db(tmp_path, monkeypatch):
    """Route every _connect()/sqlite3.connect(DATABASE_PATH) call to a
    disposable per-test SQLite file instead of the real DATABASE_PATH.
    Without this, these tests would read/write the user's actual
    production database on a local run -- DATABASE_PATH only redirects to
    a throwaway file when GITHUB_ACTIONS is set (true in CI, not on a dev
    machine).

    Patching app.config.settings.DATABASE_PATH alone would NOT work:
    images.py, folders.py, and yolo_mapping.py each do their own
    `from app.config.settings import DATABASE_PATH`, a one-time binding
    that doesn't track later changes to the original settings module
    attribute. Each module's global lookup of DATABASE_PATH resolves
    dynamically against *its own* namespace at call time, so every module
    that opens a connection needs its own attribute patched directly.
    """
    db_path = str(tmp_path / "test_image_embeddings.sqlite3")
    monkeypatch.setattr(images_module, "DATABASE_PATH", db_path)
    monkeypatch.setattr(folders_module, "DATABASE_PATH", db_path)
    monkeypatch.setattr(yolo_mapping_module, "DATABASE_PATH", db_path)
    monkeypatch.setattr(connection_module, "DATABASE_PATH", db_path)

    # images' schema FK-references folders/mappings; SQLite validates that
    # the referenced tables exist at INSERT time even for a NULL FK value,
    # so these must be created first, matching main.py's real startup order.
    db_create_YOLO_classes_table()
    db_create_folders_table()
    db_create_images_table()
    db_create_image_embeddings_table()
    yield


def _insert_dummy_image(image_id: str):
    conn = _connect()
    conn.execute(
        """
        INSERT INTO images (id, path, folder_id, thumbnailPath, metadata, isTagged, isEmbedded)
        VALUES (?, ?, NULL, ?, '{}', 0, 0)
        """,
        (image_id, f"/tmp/{image_id}.jpg", f"/tmp/{image_id}_thumb.jpg"),
    )
    conn.commit()
    conn.close()


class TestImageEmbeddingsDB:
    def test_upsert_and_get_all_embeddings_round_trip(self):
        _insert_dummy_image("img1")
        _insert_dummy_image("img2")

        emb1 = np.array([1.0, 0.0, 0.5], dtype=np.float32)
        emb2 = np.array([0.0, 1.0, -0.5], dtype=np.float32)

        db_upsert_image_embeddings(
            [
                ("img1", "siglip2-base-patch16-224", emb1),
                ("img2", "siglip2-base-patch16-224", emb2),
            ]
        )

        ids, matrix = db_get_all_embeddings("siglip2-base-patch16-224")

        assert set(ids) == {"img1", "img2"}
        assert matrix.shape == (2, 3)
        assert matrix.dtype == np.float32
        by_id = dict(zip(ids, matrix))
        assert np.array_equal(by_id["img1"], emb1)
        assert np.array_equal(by_id["img2"], emb2)

    def test_model_version_filter_excludes_other_checkpoints(self):
        _insert_dummy_image("img3")
        db_upsert_image_embeddings(
            [("img3", "siglip2-large-patch16-384", np.ones(3, dtype=np.float32))]
        )

        ids, matrix = db_get_all_embeddings("siglip2-base-patch16-224")

        assert ids == []
        assert matrix.shape == (0, 0)

        # Sanity check the row really is there, just under the other version.
        ids_large, matrix_large = db_get_all_embeddings("siglip2-large-patch16-384")
        assert ids_large == ["img3"]
        assert matrix_large.shape == (1, 3)

    def test_upsert_overwrites_existing_row_for_same_image(self):
        _insert_dummy_image("img4")
        db_upsert_image_embeddings(
            [
                (
                    "img4",
                    "siglip2-base-patch16-224",
                    np.array([1.0, 2.0, 3.0], dtype=np.float32),
                )
            ]
        )
        db_upsert_image_embeddings(
            [
                (
                    "img4",
                    "siglip2-base-patch16-224",
                    np.array([9.0, 9.0, 9.0], dtype=np.float32),
                )
            ]
        )

        ids, matrix = db_get_all_embeddings("siglip2-base-patch16-224")

        assert ids == ["img4"]
        assert np.array_equal(matrix[0], np.array([9.0, 9.0, 9.0], dtype=np.float32))

    def test_count_embeddings_with_and_without_model_version_filter(self):
        _insert_dummy_image("img5")
        _insert_dummy_image("img6")
        db_upsert_image_embeddings(
            [
                (
                    "img5",
                    "siglip2-base-patch16-224",
                    np.ones(3, dtype=np.float32),
                ),
                (
                    "img6",
                    "siglip2-large-patch16-384",
                    np.ones(3, dtype=np.float32),
                ),
            ]
        )

        assert db_count_embeddings("siglip2-base-patch16-224") == 1
        assert db_count_embeddings("siglip2-large-patch16-384") == 1
        # Now that the DB is genuinely isolated per test, this is exact --
        # no leftover rows from real usage or other tests to tolerate.
        assert db_count_embeddings() == 2

    def test_get_all_embeddings_empty_returns_empty_matrix(self):
        ids, matrix = db_get_all_embeddings("siglip2-base-patch16-224")
        assert ids == []
        assert matrix.shape == (0, 0)

    def test_deleting_image_cascades_to_its_embedding(self):
        _insert_dummy_image("img7")
        db_upsert_image_embeddings(
            [("img7", "siglip2-base-patch16-224", np.ones(3, dtype=np.float32))]
        )
        assert db_count_embeddings("siglip2-base-patch16-224") == 1

        with get_db_connection() as conn:
            conn.execute("DELETE FROM images WHERE id = ?", ("img7",))

        ids, _ = db_get_all_embeddings("siglip2-base-patch16-224")
        assert "img7" not in ids

    def test_deleting_image_cascades_to_embeddings_and_classes_regression(self):
        # 1. Insert two dummy images
        _insert_dummy_image("img7")
        _insert_dummy_image("img8")

        # 2. Insert embeddings for both
        db_upsert_image_embeddings(
            [
                ("img7", "siglip2-base-patch16-224", np.ones(3, dtype=np.float32)),
                ("img8", "siglip2-base-patch16-224", np.ones(3, dtype=np.float32)),
            ]
        )

        # 3. Insert image classes (semantic scores) for both
        with get_db_connection() as conn:
            conn.execute(
                "INSERT INTO image_classes (image_id, class_id, score) VALUES (?, 1, 0.85)",
                ("img7",),
            )
            conn.execute(
                "INSERT INTO image_classes (image_id, class_id, score) VALUES (?, 1, 0.95)",
                ("img8",),
            )

        # Verify initial state
        assert db_count_embeddings("siglip2-base-patch16-224") == 2
        with get_db_connection() as conn:
            res = conn.execute("SELECT COUNT(*) FROM image_classes").fetchone()
            assert res[0] == 2

        # 4. Call production delete logic for img7
        from app.database.images import db_delete_images_by_ids

        db_delete_images_by_ids(["img7"])

        # 5. Assert img7 cascades deleted, but img8 remains intact
        ids, _ = db_get_all_embeddings("siglip2-base-patch16-224")
        assert "img7" not in ids
        assert "img8" in ids

        with get_db_connection() as conn:
            remaining_classes = conn.execute(
                "SELECT image_id FROM image_classes"
            ).fetchall()
            assert len(remaining_classes) == 1
            assert remaining_classes[0][0] == "img8"
