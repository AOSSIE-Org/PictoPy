"""
Dirty tracking for XMP export: every write that can change an exported field
must mark exactly the affected images, and nothing else may. Each test drives
the real db_ function for its write path.
"""

import importlib
import json
import pkgutil
import sqlite3
from typing import Dict, Iterator, List, Optional, Set

import numpy as np
import pytest

import app.database as database_package
import app.database.yolo_mapping as yolo_mapping
from app.database.connection import get_db_connection
from app.database.albums import (
    db_add_images_to_album,
    db_create_album_images_table,
    db_create_album_with_images,
    db_create_albums_table,
    db_delete_album,
    db_insert_album,
    db_remove_image_from_album,
    db_remove_images_from_album,
    db_update_album,
)
from app.database.face_clusters import (
    db_create_clusters_table,
    db_delete_all_clusters,
    db_insert_clusters_batch,
    db_update_cluster,
)
from app.database.faces import (
    db_create_faces_table,
    db_insert_face_embeddings,
    db_repair_orphaned_faces,
    db_update_face_cluster_ids_batch,
)
from app.database.folders import db_create_folders_table, db_delete_folders_batch
from app.database.image_embeddings import (
    db_create_image_embeddings_table,
    db_upsert_image_embeddings,
)
from app.database.images import (
    db_bulk_insert_images,
    db_create_images_table,
    db_delete_images_by_ids,
    db_insert_image_classes_batch,
    db_mark_images_embedded,
    db_toggle_image_favourite_status,
    db_update_image_tagged_status,
)
from app.database.memories import db_create_memories_table
from app.database.metadata import db_create_metadata_table
from app.database.semantic_labels import (
    db_create_semantic_labels_table,
    db_upsert_semantic_vocabulary,
    db_write_image_semantic_scores,
)
from app.database.video_frames import (
    db_bulk_insert_video_frames,
    db_create_video_frames_tables,
)
from app.database.videos import db_create_videos_table
from app.database.xmp_export_state import (
    _TRIGGERS,
    db_create_image_xmp_state_table,
    db_get_xmp_export_candidates,
    db_record_xmp_export_failure,
    db_record_xmp_export_success,
    db_refresh_image_file_stat,
)
from app.database.yolo_mapping import db_create_YOLO_classes_table
from app.utils.face_clusters import _update_cluster_face_image

SUNSET = {"name": "sunset", "category": "scene", "descriptions": ["a sunset"]}


def _create_schema(with_state: bool = True) -> None:
    # main.py's startup order.
    db_create_folders_table()
    db_create_images_table()
    db_create_videos_table()
    db_create_semantic_labels_table()
    db_create_image_embeddings_table()
    db_create_video_frames_tables()
    db_create_YOLO_classes_table()
    db_create_clusters_table()
    db_create_faces_table()
    db_create_albums_table()
    db_create_album_images_table()
    db_create_metadata_table()
    db_create_memories_table()
    if with_state:
        db_create_image_xmp_state_table()


@pytest.fixture
def db_path(tmp_path, monkeypatch) -> Iterator[str]:
    """A throwaway database. Each database module binds DATABASE_PATH at import,
    so all of them are patched, or a local run would touch the real library."""
    path = str(tmp_path / "xmp_state.sqlite3")
    monkeypatch.setattr("app.config.settings.DATABASE_PATH", path)
    for info in pkgutil.iter_modules(database_package.__path__):
        module = importlib.import_module(f"app.database.{info.name}")
        if hasattr(module, "DATABASE_PATH"):
            monkeypatch.setattr(module, "DATABASE_PATH", path)
    # A utils module that opens its own connection.
    monkeypatch.setattr("app.utils.face_clusters.DATABASE_PATH", path)
    yield path


@pytest.fixture
def db(db_path: str) -> str:
    _create_schema()
    return db_path


def _image(
    image_id: str,
    width: int = 640,
    height: int = 480,
    ext: str = "png",
    folder_id: Optional[int] = None,
    extra: Optional[dict] = None,
) -> None:
    metadata = {"width": width, "height": height, "file_size": 100, "file_mtime": 1}
    metadata.update(extra or {})
    assert db_bulk_insert_images(
        [
            {
                "id": image_id,
                "path": f"/photos/{image_id}.{ext}",
                "folder_id": folder_id,
                "thumbnailPath": f"/thumbs/{image_id}.jpg",
                "metadata": json.dumps(metadata),
                "isTagged": False,
                "isEmbedded": False,
                "latitude": None,
                "longitude": None,
                "captured_at": None,
            }
        ]
    )


def _counts(db: str) -> Dict[str, int]:
    conn = sqlite3.connect(db)
    try:
        return dict(conn.execute("SELECT image_id, change_count FROM image_xmp_state"))
    finally:
        conn.close()


class _Watch:
    """Which images a block of writes marked dirty."""

    def __init__(self, db: str) -> None:
        self.db = db
        self.before = _counts(db)

    def marked(self) -> Set[str]:
        after = _counts(self.db)
        return {i for i, n in after.items() if n > self.before.get(i, 0)}


def _sql(db: str, statement: str, params: tuple = (), fk: bool = True) -> None:
    """Test setup only, never the write path under test."""
    conn = sqlite3.connect(db)
    try:
        conn.execute(f"PRAGMA foreign_keys = {'ON' if fk else 'OFF'}")
        conn.execute(statement, params)
        conn.commit()
    finally:
        conn.close()


def _emb(seed: float) -> np.ndarray:
    return np.full(8, seed, dtype=np.float32)


# --- write paths that must mark images ---------------------------------------


class TestTags:
    def test_yolo_tagging(self, db):
        _image("a")
        _image("b")
        watch = _Watch(db)
        db_insert_image_classes_batch([("a", 0), ("a", 16)])
        assert watch.marked() == {"a"}

    def test_semantic_rescore(self, db):
        _image("a")
        _image("b")
        db_upsert_semantic_vocabulary([SUNSET])
        watch = _Watch(db)
        db_write_image_semantic_scores([("a", [(1000, 0.4)])], "sig-1")
        assert watch.marked() == {"a"}

    def test_semantic_rescore_with_new_scores(self, db):
        _image("a")
        db_upsert_semantic_vocabulary([SUNSET])
        db_write_image_semantic_scores([("a", [(1000, 0.4)])], "sig-1")
        watch = _Watch(db)
        db_write_image_semantic_scores([("a", [(1000, 0.7)])], "sig-1")
        assert watch.marked() == {"a"}

    def test_rescore_that_removes_every_semantic_tag(self, db):
        # A delete with no insert after it: the delete trigger alone.
        _image("a")
        _image("b")
        db_upsert_semantic_vocabulary([SUNSET])
        db_write_image_semantic_scores([("a", [(1000, 0.4)])], "sig-1")
        watch = _Watch(db)
        db_write_image_semantic_scores([("a", [])], "sig-1")
        assert watch.marked() == {"a"}

    def test_label_deactivated_and_reactivated(self, db):
        _image("a")
        _image("b")
        db_upsert_semantic_vocabulary([SUNSET])
        db_write_image_semantic_scores([("a", [(1000, 0.4)])], "sig-1")

        watch = _Watch(db)
        db_upsert_semantic_vocabulary([])  # dropped from the seed
        assert watch.marked() == {"a"}

        watch = _Watch(db)
        db_upsert_semantic_vocabulary([SUNSET])
        assert watch.marked() == {"a"}

    def test_yolo_class_renamed_in_a_release(self, db, monkeypatch):
        _image("a")
        _image("b")
        db_insert_image_classes_batch([("a", 0), ("b", 1)])
        renamed = list(yolo_mapping.class_names)
        renamed[0] = "human"
        monkeypatch.setattr(yolo_mapping, "class_names", renamed)

        watch = _Watch(db)
        db_create_YOLO_classes_table()
        assert watch.marked() == {"a"}
        conn = sqlite3.connect(db)
        assert conn.execute("SELECT name FROM mappings WHERE class_id = 0").fetchone()[
            0
        ] == ("human")
        conn.close()


class TestFaces:
    def test_face_detected(self, db):
        _image("a")
        _image("b")
        watch = _Watch(db)
        db_insert_face_embeddings("a", _emb(0.1), 0.9, {"x": 1, "y": 2})
        assert watch.marked() == {"a"}

    def test_cluster_assignment(self, db):
        _image("a")
        _image("b")
        face = db_insert_face_embeddings("a", _emb(0.1))
        db_insert_clusters_batch(
            [{"cluster_id": "c1", "cluster_name": "Ann", "face_image_base64": None}]
        )
        watch = _Watch(db)
        db_update_face_cluster_ids_batch([{"face_id": face, "cluster_id": "c1"}])
        assert watch.marked() == {"a"}

    def test_full_recluster_unassigns_through_foreign_key(self, db):
        _image("a")
        _image("b")
        _image("c")
        db_insert_clusters_batch(
            [{"cluster_id": "c1", "cluster_name": "Ann", "face_image_base64": None}]
        )
        db_insert_face_embeddings("a", _emb(0.1), cluster_id="c1")
        db_insert_face_embeddings("b", _emb(0.2))  # unclustered
        watch = _Watch(db)
        # As cluster_util_face_clusters_sync does it: on a foreign-key
        # connection, so faces.cluster_id is set NULL by the FK action.
        with get_db_connection() as conn:
            db_delete_all_clusters(conn.cursor())
        assert watch.marked() == {"a"}

    def test_cluster_renamed(self, db):
        _image("a")
        _image("b")
        _image("c")
        db_insert_clusters_batch(
            [
                {"cluster_id": "c1", "cluster_name": "Ann", "face_image_base64": None},
                {"cluster_id": "c2", "cluster_name": "Bob", "face_image_base64": None},
            ]
        )
        db_insert_face_embeddings("a", _emb(0.1), cluster_id="c1")
        db_insert_face_embeddings("b", _emb(0.2), cluster_id="c1")
        db_insert_face_embeddings("c", _emb(0.3), cluster_id="c2")
        watch = _Watch(db)
        assert db_update_cluster("c1", "Anne")
        assert watch.marked() == {"a", "b"}

    def test_orphan_repair_unassigns_a_missing_cluster(self, db):
        _image("a")
        _sql(
            db,
            "INSERT INTO faces (image_id, cluster_id, embeddings) VALUES (?, ?, ?)",
            ("a", "ghost", json.dumps([0.1])),
            fk=False,
        )
        watch = _Watch(db)
        assert db_repair_orphaned_faces() == 1
        assert watch.marked() == {"a"}


class TestEmbeddings:
    def test_embedded(self, db):
        _image("a")
        _image("b")
        watch = _Watch(db)
        db_upsert_image_embeddings([("a", "m1", _emb(0.5))])
        assert watch.marked() == {"a"}

    def test_re_embedded_with_another_model(self, db):
        _image("a")
        db_upsert_image_embeddings([("a", "m1", _emb(0.5))])
        watch = _Watch(db)
        db_upsert_image_embeddings([("a", "m2", _emb(0.6))])
        assert watch.marked() == {"a"}

    def test_scored_against_a_new_vocabulary(self, db):
        _image("a")
        db_upsert_semantic_vocabulary([SUNSET])
        db_upsert_image_embeddings([("a", "m1", _emb(0.5))])
        db_write_image_semantic_scores([("a", [])], "sig-1")
        watch = _Watch(db)
        db_write_image_semantic_scores([("a", [])], "sig-2")
        assert watch.marked() == {"a"}


class TestImages:
    def test_new_image_gets_a_pending_state_row(self, db):
        _image("a")
        conn = sqlite3.connect(db)
        row = conn.execute(
            "SELECT change_count, exported_count FROM image_xmp_state WHERE image_id = 'a'"
        ).fetchone()
        conn.close()
        assert row == (0, None)

    def test_favourite_toggled(self, db):
        _image("a")
        _image("b")
        watch = _Watch(db)
        assert db_toggle_image_favourite_status("a")
        assert watch.marked() == {"a"}

    def test_rescan_with_new_dimensions(self, db):
        _image("a")
        _image("b")
        watch = _Watch(db)
        _image("a", width=1280)  # same path: the upsert's update branch
        assert watch.marked() == {"a"}

    def test_deleting_an_image_removes_its_state(self, db):
        _image("a")
        _image("b")
        db_insert_image_classes_batch([("a", 0)])
        db_insert_face_embeddings("a", _emb(0.1))
        assert db_delete_images_by_ids(["a"])
        assert set(_counts(db)) == {"b"}

    def test_deleting_a_folder_removes_its_images_state(self, db):
        _sql(db, "INSERT INTO folders (folder_id, folder_path) VALUES (7, '/p')")
        _image("a", folder_id=7)
        _image("b")
        assert db_delete_folders_batch([7]) == 1
        assert set(_counts(db)) == {"b"}


class TestAlbums:
    def test_added_and_removed(self, db):
        _image("a")
        _image("b")
        _image("c")
        db_insert_album("al", "Trip")

        watch = _Watch(db)
        db_add_images_to_album("al", ["a", "b"])
        assert watch.marked() == {"a", "b"}

        watch = _Watch(db)
        db_remove_image_from_album("al", "a")
        assert watch.marked() == {"a"}

        watch = _Watch(db)
        db_remove_images_from_album("al", ["b"])
        assert watch.marked() == {"b"}

    def test_created_with_images(self, db):
        _image("a")
        _image("b")
        watch = _Watch(db)
        db_create_album_with_images("al", "Trip", "", ["a"])
        assert watch.marked() == {"a"}

    def test_renamed(self, db):
        _image("a")
        _image("b")
        db_create_album_with_images("al", "Trip", "", ["a"])
        watch = _Watch(db)
        db_update_album("al", "Goa trip", "", False)
        assert watch.marked() == {"a"}

    def test_locked_and_unlocked(self, db):
        _image("a")
        _image("b")
        db_create_album_with_images("al", "Trip", "", ["a"])

        watch = _Watch(db)
        db_update_album("al", "Trip", "", True, "secret")
        assert watch.marked() == {"a"}

        watch = _Watch(db)
        db_update_album("al", "Trip", "", False)
        assert watch.marked() == {"a"}

    def test_deleted_through_cascade(self, db):
        _image("a")
        _image("b")
        db_create_album_with_images("al", "Trip", "", ["a"])
        watch = _Watch(db)
        db_delete_album("al")
        assert watch.marked() == {"a"}


class TestDefensiveTriggers:
    """No code path issues these writes today; the triggers guard future ones.
    Driven with plain SQL because there is no db_ function to call."""

    def test_tag_score_updated_in_place(self, db):
        _image("a")
        _image("b")
        db_upsert_semantic_vocabulary([SUNSET])
        db_write_image_semantic_scores([("a", [(1000, 0.4)])], "sig-1")
        watch = _Watch(db)
        _sql(db, "UPDATE image_classes SET score = 0.9 WHERE image_id = 'a'")
        assert watch.marked() == {"a"}

    def test_photo_face_deleted_while_image_stays(self, db):
        _image("a")
        _image("b")
        face = db_insert_face_embeddings("a", _emb(0.1))
        watch = _Watch(db)
        _sql(db, "DELETE FROM faces WHERE face_id = ?", (face,))
        assert watch.marked() == {"a"}

    def test_embedding_deleted_while_image_stays(self, db):
        _image("a")
        _image("b")
        db_upsert_image_embeddings([("a", "m1", _emb(0.5))])
        watch = _Watch(db)
        _sql(db, "DELETE FROM image_embeddings WHERE image_id = 'a'")
        assert watch.marked() == {"a"}

    def test_favourite_rewritten_unchanged(self, db):
        _image("a")
        watch = _Watch(db)
        _sql(db, "UPDATE images SET isFavourite = isFavourite")
        assert watch.marked() == set()


# --- writes that must not mark anything --------------------------------------


class TestNoFalseMarks:
    def test_startup_mapping_refresh(self, db):
        _image("a")
        db_insert_image_classes_batch([("a", 0)])
        watch = _Watch(db)
        db_create_YOLO_classes_table()
        db_create_YOLO_classes_table()
        assert watch.marked() == set()

    def test_startup_mapping_refresh_writes_nothing(self, db):
        """Not just "marks nothing": the database file itself is untouched."""
        observer = sqlite3.connect(db)
        try:
            before = observer.execute("PRAGMA data_version").fetchone()[0]
            db_create_YOLO_classes_table()
            after = observer.execute("PRAGMA data_version").fetchone()[0]
        finally:
            observer.close()
        assert after == before

    def test_rename_to_the_same_name(self, db):
        _image("a")
        db_insert_clusters_batch(
            [{"cluster_id": "c1", "cluster_name": "Ann", "face_image_base64": None}]
        )
        db_insert_face_embeddings("a", _emb(0.1), cluster_id="c1")
        watch = _Watch(db)
        db_update_cluster("c1", "Ann")
        assert watch.marked() == set()

    def test_album_description_only(self, db):
        _image("a")
        db_create_album_with_images("al", "Trip", "", ["a"])
        watch = _Watch(db)
        db_update_album("al", "Trip", "New description", False)
        assert watch.marked() == set()

    def test_cluster_cover_image(self, db):
        _image("a")
        db_insert_clusters_batch(
            [{"cluster_id": "c1", "cluster_name": "Ann", "face_image_base64": None}]
        )
        db_insert_face_embeddings("a", _emb(0.1), cluster_id="c1")
        watch = _Watch(db)
        assert _update_cluster_face_image("c1", "base64-jpeg")
        assert watch.marked() == set()

    def test_processing_flags(self, db):
        _image("a")
        watch = _Watch(db)
        db_update_image_tagged_status("a", True)
        db_mark_images_embedded(["a"])
        assert watch.marked() == set()

    def test_identical_embedding_upsert(self, db):
        _image("a")
        db_upsert_image_embeddings([("a", "m1", _emb(0.5))])
        watch = _Watch(db)
        db_upsert_image_embeddings([("a", "m1", _emb(0.5))])
        assert watch.marked() == set()

    def test_video_keyframe_face(self, db):
        _image("a")
        _sql(db, "INSERT INTO videos (id, path) VALUES ('v1', '/v1.mp4')")
        db_bulk_insert_video_frames(
            [
                {
                    "id": "f1",
                    "video_id": "v1",
                    "frame_path": "/f1.jpg",
                    "timestamp_sec": 0.0,
                    "frame_index": 0,
                }
            ]
        )
        watch = _Watch(db)
        db_insert_face_embeddings(None, _emb(0.1), frame_id="f1")
        assert watch.marked() == set()

    def test_rescan_with_unchanged_dimensions(self, db):
        _image("a")
        watch = _Watch(db)
        _image("a", extra={"file_size": 999, "file_mtime": 5})
        assert watch.marked() == set()

    def test_refreshing_file_stat_after_export(self, db):
        _image("a")
        watch = _Watch(db)
        db_refresh_image_file_stat("a", 4242, 77)
        assert watch.marked() == set()
        conn = sqlite3.connect(db)
        metadata = json.loads(
            conn.execute("SELECT metadata FROM images WHERE id = 'a'").fetchone()[0]
        )
        conn.close()
        assert (metadata["file_size"], metadata["file_mtime"]) == (4242, 77)
        assert metadata["width"] == 640


class TestRobustness:
    def test_malformed_metadata_does_not_break_a_rescan(self, db):
        _image("a")
        _sql(db, "UPDATE images SET metadata = 'not json' WHERE id = 'a'")
        _image("a", width=800)  # would raise inside the trigger without json_valid

    def test_startup_refresh_cannot_cascade_away_tags(self, db, monkeypatch):
        """The old INSERT OR REPLACE deleted every mapping row, which with
        foreign keys on takes every image's YOLO tags with it."""
        _image("a")
        db_insert_image_classes_batch([("a", 0), ("a", 16)])
        real_connect = sqlite3.connect

        def connect_with_foreign_keys(*args, **kwargs):  # type: ignore[no-untyped-def]
            conn = real_connect(*args, **kwargs)
            conn.execute("PRAGMA foreign_keys = ON")
            return conn

        monkeypatch.setattr(yolo_mapping.sqlite3, "connect", connect_with_foreign_keys)
        db_create_YOLO_classes_table()
        monkeypatch.setattr(yolo_mapping.sqlite3, "connect", real_connect)

        conn = sqlite3.connect(db)
        count = conn.execute("SELECT COUNT(*) FROM image_classes").fetchone()[0]
        conn.close()
        assert count == 2


# --- the export protocol ------------------------------------------------------


def _pending(ids: Optional[List[str]] = None) -> Dict[str, int]:
    return {c["image_id"]: c["change_count"] for c in db_get_xmp_export_candidates()}


class TestExportProtocol:
    def test_only_png_images_are_candidates(self, db):
        _image("a")
        _image("j", ext="jpg")
        _image("u", ext="PNG")
        assert set(_pending()) == {"a", "u"}

    def test_successful_export_clears_pending(self, db):
        _image("a")
        [candidate] = db_get_xmp_export_candidates()
        db_record_xmp_export_success(
            "a", candidate["change_count"], "written", "digest-1", 123, 456
        )
        assert _pending() == {}
        [clean] = db_get_xmp_export_candidates(include_clean=True)
        assert (clean["digest"], clean["file_size"], clean["file_mtime_ns"]) == (
            "digest-1",
            123,
            456,
        )

    def test_change_during_export_keeps_the_image_pending(self, db):
        _image("a")
        [candidate] = db_get_xmp_export_candidates()  # snapshot taken here
        db_toggle_image_favourite_status("a")  # lands while the file is written
        db_record_xmp_export_success(
            "a", candidate["change_count"], "written", "d", 1, 1
        )
        assert set(_pending()) == {"a"}

        [again] = db_get_xmp_export_candidates()
        db_record_xmp_export_success("a", again["change_count"], "written", "d", 1, 1)
        assert _pending() == {}

    def test_failure_keeps_the_image_pending_for_retry(self, db):
        _image("a")
        [candidate] = db_get_xmp_export_candidates()
        db_record_xmp_export_success(
            "a", candidate["change_count"], "written", "d", 1, 1
        )
        db_toggle_image_favourite_status("a")

        db_record_xmp_export_failure("a", "PermissionError: locked")
        db_record_xmp_export_failure("a", "PermissionError: locked")
        assert set(_pending()) == {"a"}
        conn = sqlite3.connect(db)
        row = conn.execute(
            "SELECT last_outcome, last_error, failure_count FROM image_xmp_state"
        ).fetchone()
        conn.close()
        assert row == ("failed", "PermissionError: locked", 2)

        [retry] = db_get_xmp_export_candidates()
        db_record_xmp_export_success("a", retry["change_count"], "written", "d", 1, 1)
        assert _pending() == {}


# --- migration and startup ----------------------------------------------------


class TestMigration:
    def test_existing_library_is_backfilled_as_never_exported(self, db_path):
        _create_schema(with_state=False)
        _image_without_state = [
            {
                "id": i,
                "path": f"/photos/{i}.png",
                "folder_id": None,
                "thumbnailPath": f"/thumbs/{i}.jpg",
                "metadata": "{}",
                "isTagged": True,
                "isEmbedded": False,
                "latitude": None,
                "longitude": None,
                "captured_at": None,
            }
            for i in ("a", "b")
        ]
        assert db_bulk_insert_images(_image_without_state)

        db_create_image_xmp_state_table()
        assert _counts(db_path) == {"a": 0, "b": 0}
        assert set(_pending()) == {"a", "b"}

    def test_second_startup_is_a_no_op(self, db):
        _image("a")
        db_insert_image_classes_batch([("a", 0)])
        [candidate] = db_get_xmp_export_candidates()
        db_record_xmp_export_success(
            "a", candidate["change_count"], "written", "d", 1, 1
        )
        before = _counts(db)

        _create_schema()  # everything main.py runs at startup, again
        assert _counts(db) == before
        assert _pending() == {}
        conn = sqlite3.connect(db)
        names = {
            r[0]
            for r in conn.execute("SELECT name FROM sqlite_master WHERE type='trigger'")
        }
        conn.close()
        assert {name for name, _ in _TRIGGERS} <= names
        assert len([n for n in names if n.startswith("xmp_")]) == len(_TRIGGERS)
