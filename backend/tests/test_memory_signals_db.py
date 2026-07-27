import os
import sqlite3
import tempfile
from contextlib import ExitStack
from typing import Iterator, List
from unittest.mock import patch

import numpy as np
import pytest

from app.routes import folders

from app.database.albums import db_create_album_images_table, db_create_albums_table
from app.database.face_clusters import db_create_clusters_table
from app.database.faces import db_create_faces_table
from app.database.folders import (
    db_clear_stale_processing_flags,
    db_create_folders_table,
    db_set_tagging_completed,
)
from app.database.image_embeddings import (
    db_create_image_embeddings_table,
    db_get_embeddings_for_image_ids,
)
from app.database.images import db_create_images_table
from app.database.memories import (
    db_create_memories_table,
    db_get_event_label_hits,
    db_get_event_labels,
    db_get_gps_cell_centre,
    db_get_gps_histogram,
    db_get_images_in_period,
    db_get_scoring_signals,
    db_get_top_event_label,
    db_is_indexing_busy,
)
from app.database.semantic_labels import (
    SEMANTIC_CLASS_ID_OFFSET,
    db_create_semantic_labels_table,
)
from app.database.yolo_mapping import db_create_YOLO_classes_table

# ##############################
# Pytest Fixtures
# ##############################


@pytest.fixture(scope="function")
def test_db(monkeypatch: pytest.MonkeyPatch) -> Iterator[str]:
    """
    A database with the whole schema the scoring query reads.

    The signal query spans faces, albums, classes and embeddings, so this
    exercises it against real SQL rather than mocks.
    """
    db_fd, db_path = tempfile.mkstemp()
    os.close(db_fd)

    # semantic_labels, image_embeddings and memories share images._connect;
    # these three modules hold their own DATABASE_PATH and need redirecting.
    for module in (
        "app.config.settings",
        "app.database.images",
        "app.database.folders",
        "app.database.yolo_mapping",
        "app.database.albums",
        "app.database.faces",
        "app.database.face_clusters",
    ):
        monkeypatch.setattr(f"{module}.DATABASE_PATH", db_path)

    db_create_YOLO_classes_table()
    db_create_folders_table()
    db_create_albums_table()
    db_create_album_images_table()
    db_create_images_table()
    db_create_clusters_table()
    db_create_faces_table()
    db_create_semantic_labels_table()
    db_create_image_embeddings_table()
    db_create_memories_table()

    yield db_path

    os.unlink(db_path)


@pytest.fixture
def images(test_db: str) -> List[str]:
    """Five images captured hourly on 2024-06-15."""
    conn = sqlite3.connect(test_db)
    conn.execute(
        "INSERT INTO folders (folder_id, folder_path, last_modified_time) "
        "VALUES ('folder-1', '/photos', 0)"
    )
    image_ids = [f"img-{i}" for i in range(5)]
    for i, image_id in enumerate(image_ids):
        conn.execute(
            "INSERT INTO images (id, path, folder_id, thumbnailPath, captured_at) "
            "VALUES (?, ?, 'folder-1', ?, ?)",
            (
                image_id,
                f"/photos/{i}.jpg",
                f"/thumbs/{i}.jpg",
                f"2024-06-15 1{i}:00:00",
            ),
        )
    conn.commit()
    conn.close()
    return image_ids


def add_semantic_label(
    db_path: str, class_id: int, name: str, category: str, active: int = 1
) -> None:
    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT OR REPLACE INTO mappings (class_id, name) VALUES (?, ?)",
        (class_id, name),
    )
    conn.execute(
        "INSERT OR REPLACE INTO semantic_labels "
        "(class_id, name, category, descriptions, threshold, active) "
        "VALUES (?, ?, ?, '[]', 0.1, ?)",
        (class_id, name, category, active),
    )
    conn.commit()
    conn.close()


def add_class_score(db_path: str, image_id: str, class_id: int, score: float) -> None:
    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT OR REPLACE INTO image_classes (image_id, class_id, score) "
        "VALUES (?, ?, ?)",
        (image_id, class_id, score),
    )
    conn.commit()
    conn.close()


def add_geotagged(
    db_path: str, prefix: str, count: int, lat: float, lon: float
) -> None:
    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT OR IGNORE INTO folders (folder_id, folder_path, last_modified_time) "
        "VALUES ('f-gps', '/gps', 0)"
    )
    conn.executemany(
        "INSERT INTO images (id, path, folder_id, thumbnailPath, latitude, longitude) "
        "VALUES (?, ?, 'f-gps', ?, ?, ?)",
        [
            (
                f"{prefix}-{i}",
                f"/gps/{prefix}{i}.jpg",
                f"/gt/{prefix}{i}.jpg",
                lat,
                lon,
            )
            for i in range(count)
        ],
    )
    conn.commit()
    conn.close()


# ##############################
# Scoring signal collection
# ##############################


class TestScoringSignals:
    def test_reports_defaults_for_a_bare_image(self, images: List[str]):
        row = db_get_scoring_signals([images[0]])[0]

        assert row["id"] == images[0]
        assert row["isFavourite"] is False
        assert row["in_album"] is False
        assert row["face_count"] == 0
        assert row["named_people"] == 0
        assert row["top_semantic_score"] is None
        assert row["top_event_score"] is None
        assert row["scored_signature"] is None

    def test_counts_faces_and_named_people_separately(
        self, test_db: str, images: List[str]
    ):
        conn = sqlite3.connect(test_db)
        conn.execute(
            "INSERT INTO face_clusters (cluster_id, cluster_name) VALUES ('c1', 'Ana')"
        )
        # A cluster the user has not named yet is not a known person.
        conn.execute(
            "INSERT INTO face_clusters (cluster_id, cluster_name) VALUES ('c2', '')"
        )
        for cluster_id in ("c1", "c2"):
            conn.execute(
                "INSERT INTO faces (image_id, cluster_id) VALUES (?, ?)",
                (images[0], cluster_id),
            )
        conn.commit()
        conn.close()

        row = db_get_scoring_signals([images[0]])[0]
        assert row["face_count"] == 2
        assert row["named_people"] == 1

    def test_reports_album_membership(self, test_db: str, images: List[str]):
        conn = sqlite3.connect(test_db)
        conn.execute("INSERT INTO albums (album_id, album_name) VALUES ('a1', 'Trip')")
        conn.execute(
            "INSERT INTO album_images (album_id, image_id) VALUES ('a1', ?)",
            (images[0],),
        )
        conn.commit()
        conn.close()

        rows = {r["id"]: r for r in db_get_scoring_signals(images[:2])}
        assert rows[images[0]]["in_album"] is True
        assert rows[images[1]]["in_album"] is False

    def test_separates_event_scores_from_general_semantic_scores(
        self, test_db: str, images: List[str]
    ):
        scene_id = SEMANTIC_CLASS_ID_OFFSET + 1
        event_id = SEMANTIC_CLASS_ID_OFFSET + 2
        add_semantic_label(test_db, scene_id, "beach", "scene")
        add_semantic_label(test_db, event_id, "wedding", "event")
        add_class_score(test_db, images[0], scene_id, 0.8)
        add_class_score(test_db, images[0], event_id, 0.4)

        row = db_get_scoring_signals([images[0]])[0]
        # top_semantic spans every semantic label; top_event only event ones.
        assert row["top_semantic_score"] == pytest.approx(0.8)
        assert row["top_event_score"] == pytest.approx(0.4)
        assert row["class_count"] == 2

    def test_yolo_classes_do_not_count_as_semantic(
        self, test_db: str, images: List[str]
    ):
        add_class_score(test_db, images[0], 5, 0.9)  # a COCO class id
        row = db_get_scoring_signals([images[0]])[0]
        assert row["top_semantic_score"] is None

    def test_reports_the_scored_signature(self, test_db: str, images: List[str]):
        conn = sqlite3.connect(test_db)
        conn.execute(
            "INSERT INTO image_embeddings "
            "(image_id, model_version, embedding, scored_signature) "
            "VALUES (?, 'v1', X'00', 'sig-1')",
            (images[0],),
        )
        conn.commit()
        conn.close()

        assert db_get_scoring_signals([images[0]])[0]["scored_signature"] == "sig-1"

    @pytest.mark.parametrize("ids", [[], ["nope"]])
    def test_empty_or_unknown_ids(self, images: List[str], ids: List[str]):
        assert db_get_scoring_signals(ids) == []

    def test_handles_more_ids_than_the_chunk_size(self, test_db: str):
        conn = sqlite3.connect(test_db)
        conn.execute(
            "INSERT INTO folders (folder_id, folder_path, last_modified_time) "
            "VALUES ('f-bulk', '/bulk', 0)"
        )
        bulk_ids = [f"bulk-{i}" for i in range(600)]
        conn.executemany(
            "INSERT INTO images (id, path, folder_id, thumbnailPath) "
            "VALUES (?, ?, 'f-bulk', ?)",
            [(i, f"/bulk/{i}.jpg", f"/bt/{i}.jpg") for i in bulk_ids],
        )
        conn.commit()
        conn.close()

        assert len(db_get_scoring_signals(bulk_ids)) == 600


# ##############################
# GPS histogram
# ##############################


class TestGpsHistogram:
    def test_orders_cells_by_density(self, test_db: str):
        add_geotagged(test_db, "home", 30, 12.9716, 77.5946)
        add_geotagged(test_db, "trip", 5, 48.8566, 2.3522)

        histogram = db_get_gps_histogram(precision=1)
        assert histogram[0][2] == 30
        assert histogram[0][:2] == (13.0, 77.6)

    def test_applies_the_minimum_count(self, test_db: str):
        add_geotagged(test_db, "few", 5, 12.9716, 77.5946)
        assert db_get_gps_histogram(precision=1, min_images=20) == []

    def test_ignores_images_without_coordinates(self, images: List[str]):
        assert db_get_gps_histogram(precision=1) == []

    def test_cell_centre_averages_the_member_images(self, test_db: str):
        # Both round to the (12.9, 77.5) cell, so the centre sits between them.
        add_geotagged(test_db, "a", 1, 12.94, 77.54)
        add_geotagged(test_db, "b", 1, 12.86, 77.46)

        centre = db_get_gps_cell_centre(12.9, 77.5, precision=1)
        assert centre is not None
        assert centre[0] == pytest.approx(12.90)
        assert centre[1] == pytest.approx(77.50)

    def test_cell_centre_ignores_images_in_other_cells(self, test_db: str):
        add_geotagged(test_db, "here", 1, 12.94, 77.54)
        add_geotagged(test_db, "far", 1, 48.86, 2.35)

        centre = db_get_gps_cell_centre(12.9, 77.5, precision=1)
        assert centre == pytest.approx((12.94, 77.54))

    def test_cell_centre_returns_none_for_an_empty_cell(self, images: List[str]):
        assert db_get_gps_cell_centre(0.0, 0.0, precision=1) is None


# ##############################
# Event labels
# ##############################


class TestEventLabels:
    def test_returns_only_active_event_labels(self, test_db: str):
        add_semantic_label(test_db, SEMANTIC_CLASS_ID_OFFSET + 1, "wedding", "event")
        add_semantic_label(test_db, SEMANTIC_CLASS_ID_OFFSET + 2, "beach", "scene")
        add_semantic_label(
            test_db, SEMANTIC_CLASS_ID_OFFSET + 3, "prom", "event", active=0
        )

        assert [label["name"] for label in db_get_event_labels()] == ["wedding"]

    def test_hits_respect_the_score_floor(self, test_db: str, images: List[str]):
        event_id = SEMANTIC_CLASS_ID_OFFSET + 1
        add_semantic_label(test_db, event_id, "wedding", "event")
        add_class_score(test_db, images[0], event_id, 0.9)
        add_class_score(test_db, images[1], event_id, 0.05)

        hits = db_get_event_label_hits([event_id], 0.15)
        assert [hit["image_id"] for hit in hits] == [images[0]]

    def test_hits_require_a_capture_time(self, test_db: str, images: List[str]):
        event_id = SEMANTIC_CLASS_ID_OFFSET + 1
        add_semantic_label(test_db, event_id, "wedding", "event")
        conn = sqlite3.connect(test_db)
        conn.execute("UPDATE images SET captured_at = NULL WHERE id = ?", (images[0],))
        conn.commit()
        conn.close()
        add_class_score(test_db, images[0], event_id, 0.9)

        assert db_get_event_label_hits([event_id], 0.15) == []

    def test_no_class_ids_returns_nothing(self, test_db: str):
        assert db_get_event_label_hits([], 0.15) == []

    def test_top_event_label_picks_the_strongest_by_total(
        self, test_db: str, images: List[str]
    ):
        """Summed, not peak: a label seen across the set beats one strong hit."""
        broad = SEMANTIC_CLASS_ID_OFFSET + 1
        narrow = SEMANTIC_CLASS_ID_OFFSET + 2
        add_semantic_label(test_db, broad, "birthday", "event")
        add_semantic_label(test_db, narrow, "picnic", "event")
        for image_id in images[:3]:
            add_class_score(test_db, image_id, broad, 0.6)
        add_class_score(test_db, images[0], narrow, 0.9)

        result = db_get_top_event_label(images, 0.15)
        assert result is not None
        assert result[1] == "birthday"

    @pytest.mark.parametrize("ids", [[], ["img-0"]])
    def test_top_event_label_is_none_without_matches(
        self, images: List[str], ids: List[str]
    ):
        assert db_get_top_event_label(ids, 0.15) is None


# ##############################
# Tagging completion lifecycle
# ##############################


@pytest.fixture
def ai_folder(test_db: str) -> str:
    """A folder with AI tagging enabled and tagging not yet finished."""
    conn = sqlite3.connect(test_db)
    conn.execute(
        "INSERT INTO folders (folder_id, folder_path, last_modified_time, "
        "AI_Tagging, taggingCompleted, indexing_status) "
        "VALUES ('f-ai', '/ai', 0, 1, 0, 'completed')"
    )
    conn.commit()
    conn.close()
    return "f-ai"


class TestTaggingCompletedLifecycle:
    """
    The indexing gate reads folders.taggingCompleted. Nothing wrote that
    column after insert, so every AI-tagged folder read as permanently
    mid-tagging and memory generation stayed blocked forever.
    """

    def test_flag_toggles(self, ai_folder: str, test_db: str):
        assert db_is_indexing_busy() is True

        assert db_set_tagging_completed(True) == 1
        assert db_is_indexing_busy() is False

        assert db_set_tagging_completed(False) == 1
        assert db_is_indexing_busy() is True

    def test_ignores_folders_without_ai_tagging(self, test_db: str):
        conn = sqlite3.connect(test_db)
        conn.execute(
            "INSERT INTO folders (folder_id, folder_path, last_modified_time, "
            "AI_Tagging) VALUES ('f-plain', '/plain', 0, 0)"
        )
        conn.commit()
        conn.close()

        assert db_set_tagging_completed(True) == 0

    def _run_tagging(self, fail_at: str = "") -> List[bool]:
        """Run the tagging sequence, sampling the gate at each step."""
        observed: List[bool] = []
        with ExitStack() as stack:
            for step in AI_PIPELINE_STEPS:
                stack.enter_context(
                    patch.object(
                        folders,
                        step,
                        side_effect=(
                            Exception("boom")
                            if step == fail_at
                            else (lambda *_: observed.append(db_is_indexing_busy()))
                        ),
                    )
                )
            stack.enter_context(patch.object(folders, "_curate_memories"))
            self.result = folders.post_AI_tagging_enabled_sequence()
        return observed

    def test_gate_is_busy_during_tagging_and_clears_after(self, ai_folder: str):
        observed = self._run_tagging()

        assert observed and all(observed), "gate must stay busy while tagging runs"
        assert self.result is True
        assert db_is_indexing_busy() is False

    def test_a_failed_run_still_clears_the_gate(self, ai_folder: str):
        """A folder that failed to tag is not still tagging."""
        self._run_tagging(fail_at="image_util_process_untagged_images")

        assert self.result is False
        assert db_is_indexing_busy() is False

    def test_startup_clears_flags_left_by_an_earlier_session(self, ai_folder: str):
        """
        Setting the flag when tagging ends does nothing for a library whose
        tagging already finished under the older code. Startup has to correct
        those rows or they stay blocked forever.
        """
        assert db_is_indexing_busy() is True

        assert db_clear_stale_processing_flags() == 1
        assert db_is_indexing_busy() is False

    def test_startup_clears_an_interrupted_index(self, test_db: str):
        conn = sqlite3.connect(test_db)
        conn.execute(
            "INSERT INTO folders (folder_id, folder_path, last_modified_time, "
            "AI_Tagging, indexing_status) VALUES ('f-killed', '/killed', 0, 0, "
            "'in_progress')"
        )
        conn.commit()
        conn.close()

        assert db_is_indexing_busy() is True
        assert db_clear_stale_processing_flags() == 1
        assert db_is_indexing_busy() is False

    def test_startup_is_idempotent_and_spares_untagged_folders(self, test_db: str):
        conn = sqlite3.connect(test_db)
        conn.execute(
            "INSERT INTO folders (folder_id, folder_path, last_modified_time, "
            "AI_Tagging, taggingCompleted) VALUES ('f-plain', '/plain', 0, 0, 0)"
        )
        conn.commit()
        conn.close()

        assert db_clear_stale_processing_flags() == 0
        assert db_clear_stale_processing_flags() == 0

        conn = sqlite3.connect(test_db)
        completed = conn.execute(
            "SELECT taggingCompleted FROM folders WHERE folder_id = 'f-plain'"
        ).fetchone()[0]
        conn.close()
        # Never AI-tagged, so the flag is meaningless and must stay untouched.
        assert completed == 0

    def test_sync_clears_the_gate_too(self, ai_folder: str):
        with ExitStack() as stack:
            for step in (
                "image_util_process_folder_images",
                "video_util_process_folder_videos",
                "API_util_restart_sync_microservice_watcher",
                "_curate_memories",
                *AI_PIPELINE_STEPS[1:],
            ):
                stack.enter_context(patch.object(folders, step))
            assert folders.post_sync_folder_sequence("/ai", 1, []) is True

        assert db_is_indexing_busy() is False


# ##############################
# Period lookup and embeddings
# ##############################


class TestPeriodAndEmbeddings:
    def test_returns_images_inside_the_span(self, images: List[str]):
        found = db_get_images_in_period("2024-06-15 11:00:00", "2024-06-15 13:00:00")
        assert [image["id"] for image in found] == images[1:4]

    def test_honours_the_exclusion_list(self, images: List[str]):
        found = db_get_images_in_period(
            "2024-06-15 10:00:00", "2024-06-15 20:00:00", exclude_ids=images[:2]
        )
        assert [image["id"] for image in found] == images[2:]

    @pytest.mark.parametrize(
        "start, end",
        [
            ("2024-06-15 11:00:00", "2024-06-15 13:00:00"),  # space separator
            ("2024-06-15T11:00:00", "2024-06-15T13:00:00"),  # ISO "T"
        ],
    )
    def test_accepts_either_timestamp_separator(
        self, images: List[str], start: str, end: str
    ):
        """
        Callers pass datetime.isoformat(), which uses "T", while stored values
        use a space. Compared as raw strings that matches nothing, because "T"
        sorts after every digit.
        """
        found = db_get_images_in_period(start, end)
        assert [image["id"] for image in found] == images[1:4]

    def test_boundaries_are_inclusive(self, images: List[str]):
        found = db_get_images_in_period("2024-06-15T11:00:00", "2024-06-15T12:00:00")
        assert [image["id"] for image in found] == images[1:3]

    def test_embeddings_are_returned_only_for_the_matching_model(
        self, test_db: str, images: List[str]
    ):
        vector = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        conn = sqlite3.connect(test_db)
        for image_id, model in ((images[0], "v1"), (images[1], "v2")):
            conn.execute(
                "INSERT INTO image_embeddings (image_id, model_version, embedding) "
                "VALUES (?, ?, ?)",
                (image_id, model, vector.tobytes()),
            )
        conn.commit()
        conn.close()

        found = db_get_embeddings_for_image_ids(images, "v1")
        assert set(found) == {images[0]}
        assert np.allclose(found[images[0]], vector)

    def test_embeddings_empty_input(self, test_db: str):
        assert db_get_embeddings_for_image_ids([], "v1") == {}


# ##############################
# Folder pipeline hook
# ##############################


AI_PIPELINE_STEPS = (
    "ensure_ai_tagging_models",
    "image_util_process_untagged_images",
    "cluster_util_face_clusters_sync",
    "image_util_process_unembedded_images",
    "semantic_util_score_images",
    "video_util_process_untagged_videos",
    "video_util_process_unembedded_frames",
    "semantic_util_score_videos",
)


class TestCurationHook:
    def test_swallows_curation_failures(self):
        """A curation problem must never fail the import that triggered it."""
        with patch(
            "app.utils.memory_curator.memory_curator_run",
            side_effect=Exception("boom"),
        ):
            folders._curate_memories("test")  # must not raise

    def test_forces_regeneration(self):
        with patch(
            "app.utils.memory_curator.memory_curator_run", return_value=2
        ) as run:
            folders._curate_memories("ai_tagging")

        # New photos arrived, so existing memories must be re-evaluated.
        run.assert_called_once_with(force=True, trigger="ai_tagging")

    def test_ai_tagging_pipeline_curates_after_scoring_before_videos(self):
        """
        Curation needs semantic labels written, and the video pass can run for
        minutes, so it belongs between the two.
        """
        order: List[str] = []
        with ExitStack() as stack:
            for step in AI_PIPELINE_STEPS:
                stack.enter_context(
                    patch.object(
                        folders,
                        step,
                        side_effect=lambda *_, _s=step: order.append(_s),
                    )
                )
            stack.enter_context(
                patch.object(
                    folders,
                    "_curate_memories",
                    side_effect=lambda trigger: order.append(f"curate:{trigger}"),
                )
            )
            assert folders.post_AI_tagging_enabled_sequence() is True

        assert order.index("semantic_util_score_images") < order.index(
            "curate:ai_tagging"
        )
        assert order.index("curate:ai_tagging") < order.index(
            "video_util_process_untagged_videos"
        )

    def test_folder_add_pipeline_curates_after_indexing_completes(self):
        """
        No AI has run here, so only the date-driven triggers can produce
        anything; it still has to run so new photos surface.
        """
        order: List[str] = []
        with ExitStack() as stack:
            stack.enter_context(
                patch.object(
                    folders,
                    "db_get_folder_ids_by_path_prefix",
                    return_value=[("f-1", "/photos")],
                )
            )
            stack.enter_context(
                patch.object(
                    folders,
                    "db_update_folder_indexing_status",
                    side_effect=lambda _id, status: order.append(f"status:{status}"),
                )
            )
            for step in (
                "image_util_process_folder_images",
                "video_util_process_folder_videos",
                "API_util_restart_sync_microservice_watcher",
            ):
                stack.enter_context(patch.object(folders, step))
            stack.enter_context(
                patch.object(
                    folders,
                    "_curate_memories",
                    side_effect=lambda trigger: order.append(f"curate:{trigger}"),
                )
            )
            assert folders.post_folder_add_sequence("/photos", 1) is True

        assert order.index("status:completed") < order.index("curate:folder_add")

    def test_sync_pipeline_curates_after_scoring(self):
        order: List[str] = []
        with ExitStack() as stack:
            for step in (
                "image_util_process_folder_images",
                "video_util_process_folder_videos",
                "API_util_restart_sync_microservice_watcher",
                *AI_PIPELINE_STEPS[1:],
            ):
                stack.enter_context(
                    patch.object(
                        folders,
                        step,
                        side_effect=lambda *_, _s=step: order.append(_s),
                    )
                )
            stack.enter_context(
                patch.object(
                    folders,
                    "_curate_memories",
                    side_effect=lambda trigger: order.append(f"curate:{trigger}"),
                )
            )
            assert folders.post_sync_folder_sequence("/photos", 1, []) is True

        assert order.index("semantic_util_score_images") < order.index(
            "curate:sync_folder"
        )
