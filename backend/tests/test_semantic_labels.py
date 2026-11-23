import numpy as np
import pytest

import app.database.images as images_module
import app.database.folders as folders_module
import app.database.yolo_mapping as yolo_mapping_module
from app.database.images import _connect, db_create_images_table
from app.database.folders import db_create_folders_table
from app.database.yolo_mapping import db_create_YOLO_classes_table
from app.database.semantic_labels import (
    SEMANTIC_CLASS_ID_OFFSET,
    db_create_semantic_labels_table,
    db_upsert_semantic_vocabulary,
    db_get_labels_needing_embeddings,
    db_update_label_embeddings,
    db_get_active_label_embeddings,
)
from app.database.image_embeddings import (
    db_create_image_embeddings_table,
    db_upsert_image_embeddings,
)
from app.utils.semantic_labels import semantic_util_score_images

MODEL_VERSION = "siglip2-base-patch16-224"


@pytest.fixture(autouse=True)
def _isolated_db(tmp_path, monkeypatch):
    """Same isolation pattern as test_image_embeddings.py: every module that
    opens a connection needs its own DATABASE_PATH attribute patched."""
    db_path = str(tmp_path / "test_semantic_labels.sqlite3")
    monkeypatch.setattr(images_module, "DATABASE_PATH", db_path)
    monkeypatch.setattr(folders_module, "DATABASE_PATH", db_path)
    monkeypatch.setattr(yolo_mapping_module, "DATABASE_PATH", db_path)

    db_create_YOLO_classes_table()
    db_create_folders_table()
    db_create_images_table()
    db_create_semantic_labels_table()
    db_create_image_embeddings_table()
    yield


def _label(name, category="scene", descriptions=None, threshold=None):
    entry = {
        "name": name,
        "category": category,
        "descriptions": descriptions or [f"a photo of a {name}"],
    }
    if threshold is not None:
        entry["threshold"] = threshold
    return entry


def _fetch(sql, params=()):
    conn = _connect()
    try:
        return conn.execute(sql, params).fetchall()
    finally:
        conn.close()


class TestSchemaMigration:
    def test_old_shell_schema_is_dropped_and_recreated(self):
        conn = _connect()
        conn.execute("DROP TABLE semantic_labels")
        conn.execute(
            """
            CREATE TABLE semantic_labels (
                label_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                prompt_template TEXT,
                threshold REAL,
                active BOOLEAN DEFAULT 1
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE image_semantic_labels (
                image_id TEXT,
                label_id INTEGER,
                score REAL NOT NULL,
                PRIMARY KEY (image_id, label_id)
            )
            """
        )
        conn.commit()
        conn.close()

        db_create_semantic_labels_table()

        columns = {row[1] for row in _fetch("PRAGMA table_info(semantic_labels)")}
        assert "descriptions" in columns
        assert "label_embedding" in columns
        assert "prompt_template" not in columns
        tables = {
            row[0]
            for row in _fetch("SELECT name FROM sqlite_master WHERE type='table'")
        }
        assert "image_semantic_labels" not in tables

    def test_new_schema_is_left_untouched(self):
        db_upsert_semantic_vocabulary([_label("beach")])
        db_create_semantic_labels_table()
        assert _fetch("SELECT name FROM semantic_labels") == [("beach",)]

    def test_image_classes_gains_score_column(self):
        columns = {row[1] for row in _fetch("PRAGMA table_info(image_classes)")}
        assert "score" in columns


class TestVocabularyUpsert:
    def test_new_labels_registered_in_mappings_above_offset(self):
        db_upsert_semantic_vocabulary([_label("beach"), _label("diwali", "event")])

        rows = _fetch(
            "SELECT m.class_id, m.name FROM mappings m "
            "JOIN semantic_labels s ON s.class_id = m.class_id ORDER BY m.class_id"
        )
        assert [name for _, name in rows] == ["beach", "diwali"]
        assert all(cid >= SEMANTIC_CLASS_ID_OFFSET for cid, _ in rows)

    def test_upsert_is_idempotent(self):
        labels = [_label("beach"), _label("diwali", "event")]
        db_upsert_semantic_vocabulary(labels)
        first = _fetch("SELECT class_id, name FROM semantic_labels ORDER BY name")
        db_upsert_semantic_vocabulary(labels)
        assert (
            _fetch("SELECT class_id, name FROM semantic_labels ORDER BY name") == first
        )

    def test_description_change_invalidates_cached_embedding(self):
        db_upsert_semantic_vocabulary([_label("beach")])
        class_id = _fetch("SELECT class_id FROM semantic_labels")[0][0]
        db_update_label_embeddings(
            [(class_id, np.ones(4, dtype=np.float32), MODEL_VERSION)]
        )

        # unchanged descriptions keep the cache
        db_upsert_semantic_vocabulary([_label("beach")])
        assert _fetch("SELECT label_embedding FROM semantic_labels")[0][0] is not None

        db_upsert_semantic_vocabulary(
            [_label("beach", descriptions=["waves on a sandy shore"])]
        )
        row = _fetch(
            "SELECT label_embedding, embedding_model_version FROM semantic_labels"
        )[0]
        assert row == (None, None)

    def test_label_missing_from_seed_is_deactivated_and_reactivated(self):
        db_upsert_semantic_vocabulary([_label("beach"), _label("diwali", "event")])
        db_upsert_semantic_vocabulary([_label("beach")])
        assert _fetch("SELECT active FROM semantic_labels WHERE name = 'diwali'") == [
            (0,)
        ]

        db_upsert_semantic_vocabulary([_label("beach"), _label("diwali", "event")])
        assert _fetch("SELECT active FROM semantic_labels WHERE name = 'diwali'") == [
            (1,)
        ]

    def test_yolo_owned_name_is_skipped(self):
        db_upsert_semantic_vocabulary([_label("person"), _label("beach")])
        assert _fetch("SELECT name FROM semantic_labels") == [("beach",)]

    def test_orphan_mapping_row_is_reused(self):
        # a semantic mapping surviving a semantic_labels drop keeps its id,
        # so existing image_classes rows stay linked
        orphan_id = SEMANTIC_CLASS_ID_OFFSET + 7
        conn = _connect()
        conn.execute(
            "INSERT INTO mappings (class_id, name) VALUES (?, 'beach')",
            (orphan_id,),
        )
        conn.commit()
        conn.close()

        db_upsert_semantic_vocabulary([_label("beach")])
        assert _fetch("SELECT class_id FROM semantic_labels") == [(orphan_id,)]
        assert len(_fetch("SELECT class_id FROM mappings WHERE name = 'beach'")) == 1


class TestLabelEmbeddings:
    def test_needing_embeddings_tracks_staleness(self):
        db_upsert_semantic_vocabulary(
            [_label("beach", descriptions=["a", "b"]), _label("diwali", "event")]
        )
        stale = db_get_labels_needing_embeddings(MODEL_VERSION)
        assert sorted(descs for _, descs in stale) == [
            ["a", "b"],
            ["a photo of a diwali"],
        ]

        for class_id, _ in stale:
            db_update_label_embeddings(
                [(class_id, np.ones(4, dtype=np.float32), MODEL_VERSION)]
            )
        assert db_get_labels_needing_embeddings(MODEL_VERSION) == []
        # a checkpoint swap makes every cached embedding stale again
        assert len(db_get_labels_needing_embeddings("other-checkpoint")) == 2

    def test_active_label_embeddings_round_trip(self):
        db_upsert_semantic_vocabulary(
            [_label("beach", threshold=0.05), _label("diwali", "event")]
        )
        rows = _fetch("SELECT class_id, name FROM semantic_labels ORDER BY name")
        beach_id = rows[0][0]

        beach_vec = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        db_update_label_embeddings([(beach_id, beach_vec, MODEL_VERSION)])

        meta, matrix = db_get_active_label_embeddings(MODEL_VERSION)
        # diwali has no cached embedding yet, so only beach comes back
        assert meta == [(beach_id, "scene", 0.05)]
        np.testing.assert_array_equal(matrix, beach_vec.reshape(1, -1))
        assert matrix.dtype == np.float32

        # wrong checkpoint returns nothing
        meta, matrix = db_get_active_label_embeddings("other-checkpoint")
        assert meta == [] and matrix.size == 0


def _insert_image_with_embedding(image_id: str, vec: np.ndarray):
    conn = _connect()
    conn.execute(
        "INSERT INTO images (id, path, folder_id, thumbnailPath, metadata, "
        "isTagged, isEmbedded) VALUES (?, ?, NULL, ?, '{}', 0, 1)",
        (image_id, f"/tmp/{image_id}.jpg", f"/tmp/{image_id}_thumb.jpg"),
    )
    conn.commit()
    conn.close()
    db_upsert_image_embeddings([(image_id, MODEL_VERSION, vec)])


def _unit(dim: int, size: int = 8) -> np.ndarray:
    v = np.zeros(size, dtype=np.float32)
    v[dim] = 1.0
    return v


class TestScoringPass:
    def _seed_labels(self):
        """Three scene labels with one-hot embeddings on dims 0, 1, 2."""
        db_upsert_semantic_vocabulary(
            [_label("beach"), _label("forest"), _label("desert")]
        )
        ids = dict(_fetch("SELECT name, class_id FROM semantic_labels"))
        db_update_label_embeddings(
            [
                (ids["beach"], _unit(0), MODEL_VERSION),
                (ids["forest"], _unit(1), MODEL_VERSION),
                (ids["desert"], _unit(2), MODEL_VERSION),
            ]
        )
        return ids

    def _image_tags(self, image_id):
        return dict(
            _fetch(
                "SELECT class_id, score FROM image_classes "
                "WHERE image_id = ? AND class_id >= ?",
                (image_id, SEMANTIC_CLASS_ID_OFFSET),
            )
        )

    def test_writes_above_threshold_topk_rows(self):
        ids = self._seed_labels()
        # strong beach (score saturates ~1), mid-range forest (cosine 0.13
        # -> sigmoid ~0.13, above threshold but unsaturated), zero desert
        vec = np.zeros(8, dtype=np.float32)
        vec[0], vec[1] = 0.9, 0.12
        _insert_image_with_embedding("img1", vec / np.linalg.norm(vec))

        semantic_util_score_images()

        tags = self._image_tags("img1")
        assert set(tags) == {ids["beach"], ids["forest"]}
        assert tags[ids["beach"]] > tags[ids["forest"]] > 0
        sig = _fetch(
            "SELECT scored_signature FROM image_embeddings WHERE image_id='img1'"
        )[0][0]
        assert sig

    def test_top_k_caps_writes(self, monkeypatch):
        import app.config.settings as settings

        monkeypatch.setattr(settings, "SEMANTIC_SCORE_TOP_K", 1)
        ids = self._seed_labels()
        vec = np.zeros(8, dtype=np.float32)
        vec[0], vec[1] = 0.9, 0.12
        _insert_image_with_embedding("img1", vec / np.linalg.norm(vec))

        semantic_util_score_images()

        assert set(self._image_tags("img1")) == {ids["beach"]}

    def test_idempotent_and_rescore_on_label_change(self):
        ids = self._seed_labels()
        _insert_image_with_embedding("img1", _unit(0))
        semantic_util_score_images()

        # simulate manual row loss: an unchanged signature must NOT rewrite
        conn = _connect()
        conn.execute(
            "DELETE FROM image_classes WHERE image_id='img1' AND class_id >= ?",
            (SEMANTIC_CLASS_ID_OFFSET,),
        )
        conn.commit()
        conn.close()
        semantic_util_score_images()
        assert self._image_tags("img1") == {}

        # a label embedding CONTENT change alters the signature -> re-score
        db_update_label_embeddings([(ids["forest"], _unit(3), MODEL_VERSION)])
        semantic_util_score_images()
        assert ids["beach"] in self._image_tags("img1")

    def test_deactivated_label_rows_removed_on_rescore(self):
        ids = self._seed_labels()
        _insert_image_with_embedding("img1", _unit(2))
        semantic_util_score_images()
        assert set(self._image_tags("img1")) == {ids["desert"]}

        # desert missing from the new seed -> deactivated -> new signature
        db_upsert_semantic_vocabulary([_label("beach"), _label("forest")])
        semantic_util_score_images()
        assert self._image_tags("img1") == {}

    def test_yolo_rows_survive_scoring(self):
        ids = self._seed_labels()
        _insert_image_with_embedding("img1", _unit(0))
        conn = _connect()
        conn.execute(
            "INSERT INTO image_classes (image_id, class_id) VALUES ('img1', 0)"
        )
        conn.commit()
        conn.close()

        semantic_util_score_images()

        rows = _fetch(
            "SELECT class_id, score FROM image_classes "
            "WHERE image_id='img1' ORDER BY class_id"
        )
        assert rows[0] == (0, None)  # YOLO row intact, no score
        assert rows[1][0] == ids["beach"]

    def test_no_label_embeddings_is_a_noop(self):
        db_upsert_semantic_vocabulary([_label("beach")])  # no embeddings built
        _insert_image_with_embedding("img1", _unit(0))
        semantic_util_score_images()
        assert self._image_tags("img1") == {}
        sig = _fetch(
            "SELECT scored_signature FROM image_embeddings WHERE image_id='img1'"
        )[0][0]
        assert sig is None


class TestDisplayCut:
    def test_view_cuts_semantic_tags_but_keeps_yolo_and_search_matching(self):
        from app.database.images import db_search_images_by_tag

        names = [f"label{i}" for i in range(7)]
        db_upsert_semantic_vocabulary([_label(n) for n in names])
        ids = dict(_fetch("SELECT name, class_id FROM semantic_labels"))
        _insert_image_with_embedding("img1", _unit(0))

        conn = _connect()
        # 7 semantic rows with descending scores + one YOLO row
        for rank, name in enumerate(names):
            conn.execute(
                "INSERT INTO image_classes (image_id, class_id, score) "
                "VALUES ('img1', ?, ?)",
                (ids[name], 0.9 - rank * 0.1),
            )
        conn.execute(
            "INSERT INTO image_classes (image_id, class_id) VALUES ('img1', 0)"
        )
        conn.commit()
        conn.close()

        shown = _fetch(
            "SELECT class_id FROM image_classes_display WHERE image_id='img1'"
        )
        shown_ids = {c for (c,) in shown}
        # all 5 top-scored semantic labels + the YOLO row, ranks 6-7 cut
        assert shown_ids == {0} | {ids[n] for n in names[:5]}

        # a below-the-cut tag still matches in search (full table)...
        hits = db_search_images_by_tag("label6")
        assert [h["id"] for h in hits] == ["img1"]
        # ...but the returned display tag list respects the cut
        assert "label6" not in hits[0]["tags"]
        assert "label0" in hits[0]["tags"]
