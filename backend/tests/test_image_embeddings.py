import numpy as np
import pytest

from app.database.images import _connect
from app.database.image_embeddings import (
    db_create_image_embeddings_table,
    db_upsert_image_embeddings,
    db_get_all_embeddings,
    db_count_embeddings,
)


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


@pytest.fixture(autouse=True)
def _isolate_embeddings_table():
    db_create_image_embeddings_table()
    conn = _connect()
    conn.execute("DELETE FROM image_embeddings")
    conn.execute("DELETE FROM images WHERE id LIKE 'emb_test_%'")
    conn.commit()
    conn.close()
    yield
    conn = _connect()
    conn.execute("DELETE FROM image_embeddings")
    conn.execute("DELETE FROM images WHERE id LIKE 'emb_test_%'")
    conn.commit()
    conn.close()


class TestImageEmbeddingsDB:
    def test_upsert_and_get_all_embeddings_round_trip(self):
        _insert_dummy_image("emb_test_1")
        _insert_dummy_image("emb_test_2")

        emb1 = np.array([1.0, 0.0, 0.5], dtype=np.float32)
        emb2 = np.array([0.0, 1.0, -0.5], dtype=np.float32)

        db_upsert_image_embeddings(
            [
                ("emb_test_1", "siglip2-base-patch16-224", emb1),
                ("emb_test_2", "siglip2-base-patch16-224", emb2),
            ]
        )

        ids, matrix = db_get_all_embeddings("siglip2-base-patch16-224")

        assert set(ids) == {"emb_test_1", "emb_test_2"}
        assert matrix.shape == (2, 3)
        assert matrix.dtype == np.float32
        by_id = dict(zip(ids, matrix))
        assert np.array_equal(by_id["emb_test_1"], emb1)
        assert np.array_equal(by_id["emb_test_2"], emb2)

    def test_model_version_filter_excludes_other_checkpoints(self):
        _insert_dummy_image("emb_test_3")
        db_upsert_image_embeddings(
            [("emb_test_3", "siglip2-large-patch16-384", np.ones(3, dtype=np.float32))]
        )

        ids, matrix = db_get_all_embeddings("siglip2-base-patch16-224")

        assert ids == []
        assert matrix.shape == (0, 0)

        # Sanity check the row really is there, just under the other version.
        ids_large, matrix_large = db_get_all_embeddings("siglip2-large-patch16-384")
        assert ids_large == ["emb_test_3"]
        assert matrix_large.shape == (1, 3)

    def test_upsert_overwrites_existing_row_for_same_image(self):
        _insert_dummy_image("emb_test_4")
        db_upsert_image_embeddings(
            [
                (
                    "emb_test_4",
                    "siglip2-base-patch16-224",
                    np.array([1.0, 2.0, 3.0], dtype=np.float32),
                )
            ]
        )
        db_upsert_image_embeddings(
            [
                (
                    "emb_test_4",
                    "siglip2-base-patch16-224",
                    np.array([9.0, 9.0, 9.0], dtype=np.float32),
                )
            ]
        )

        ids, matrix = db_get_all_embeddings("siglip2-base-patch16-224")

        assert ids == ["emb_test_4"]
        assert np.array_equal(matrix[0], np.array([9.0, 9.0, 9.0], dtype=np.float32))

    def test_count_embeddings_with_and_without_model_version_filter(self):
        _insert_dummy_image("emb_test_5")
        _insert_dummy_image("emb_test_6")
        db_upsert_image_embeddings(
            [
                (
                    "emb_test_5",
                    "siglip2-base-patch16-224",
                    np.ones(3, dtype=np.float32),
                ),
                (
                    "emb_test_6",
                    "siglip2-large-patch16-384",
                    np.ones(3, dtype=np.float32),
                ),
            ]
        )

        assert db_count_embeddings("siglip2-base-patch16-224") == 1
        assert db_count_embeddings("siglip2-large-patch16-384") == 1
        assert db_count_embeddings() >= 2

    def test_get_all_embeddings_empty_returns_empty_matrix(self):
        ids, matrix = db_get_all_embeddings("siglip2-base-patch16-224")
        assert ids == []
        assert matrix.shape == (0, 0)

    def test_deleting_image_cascades_to_its_embedding(self):
        _insert_dummy_image("emb_test_7")
        db_upsert_image_embeddings(
            [("emb_test_7", "siglip2-base-patch16-224", np.ones(3, dtype=np.float32))]
        )
        assert db_count_embeddings("siglip2-base-patch16-224") == 1

        conn = _connect()
        conn.execute("DELETE FROM images WHERE id = ?", ("emb_test_7",))
        conn.commit()
        conn.close()

        ids, _ = db_get_all_embeddings("siglip2-base-patch16-224")
        assert "emb_test_7" not in ids
