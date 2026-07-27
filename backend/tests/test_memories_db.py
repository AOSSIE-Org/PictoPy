import os
import sqlite3
import tempfile
import uuid
from typing import Any, Dict, Iterator, List, Optional, Sequence, Tuple

import pytest

from app.database.folders import db_create_folders_table
from app.database.images import db_create_images_table, db_delete_images_by_ids
from app.database.memories import (
    db_count_unviewed_memories,
    db_create_memories_table,
    db_delete_memory,
    db_finish_memory_run,
    db_get_anniversary_candidates,
    db_get_existing_dedupe_keys,
    db_get_memory,
    db_get_memory_images,
    db_get_memory_run,
    db_get_recently_used_image_ids,
    db_get_surfaceable_memory,
    db_is_indexing_busy,
    db_list_memories,
    db_mark_memory,
    db_prune_empty_memories,
    db_reap_stale_memory_runs,
    db_start_memory_run,
    db_upsert_memory,
)
from app.database.yolo_mapping import db_create_YOLO_classes_table

# ##############################
# Pytest Fixtures
# ##############################


@pytest.fixture(scope="function")
def test_db(monkeypatch: pytest.MonkeyPatch) -> Iterator[str]:
    """Point the memory/image DB modules at a fresh tempfile database."""
    db_fd, db_path = tempfile.mkstemp()
    os.close(db_fd)

    monkeypatch.setattr("app.config.settings.DATABASE_PATH", db_path)
    monkeypatch.setattr("app.database.images.DATABASE_PATH", db_path)
    monkeypatch.setattr("app.database.folders.DATABASE_PATH", db_path)
    monkeypatch.setattr("app.database.yolo_mapping.DATABASE_PATH", db_path)

    db_create_YOLO_classes_table()
    db_create_folders_table()
    db_create_images_table()
    db_create_memories_table()

    yield db_path

    os.unlink(db_path)


@pytest.fixture
def images(test_db: str) -> List[str]:
    """Insert a folder plus five images and return their ids."""
    conn = sqlite3.connect(test_db)
    conn.execute(
        "INSERT INTO folders (folder_id, folder_path, last_modified_time, AI_Tagging) "
        "VALUES ('folder-1', '/photos', 0, 1)"
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


def make_memory(dedupe_key: str, **overrides: Any) -> Dict[str, Any]:
    memory: Dict[str, Any] = {
        "memory_id": str(uuid.uuid4()),
        "dedupe_key": dedupe_key,
        "event_type": "anniversary",
        "status": "complete",
        "title": "2 years ago today",
        "surface_date": "2026-07-26",
        "score": 0.5,
    }
    memory.update(overrides)
    return memory


def entries(image_ids: Sequence[str]) -> List[Tuple[str, int, Optional[float]]]:
    return [(image_id, i, 1.0 - i * 0.1) for i, image_id in enumerate(image_ids)]


def set_started_at(db_path: str, run_date: str, expression: str) -> None:
    """Backdate a run's start time so staleness can be exercised."""
    conn = sqlite3.connect(db_path)
    conn.execute(
        f"UPDATE memory_runs SET started_at = {expression} WHERE run_date = ?",
        (run_date,),
    )
    conn.commit()
    conn.close()


# ##############################
# Table creation
# ##############################


class TestCreateMemoriesTable:
    def test_creation_is_idempotent(self, test_db: str):
        db_create_memories_table()
        db_create_memories_table()

        conn = sqlite3.connect(test_db)
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        conn.close()
        assert {"memories", "memory_images", "memory_runs"} <= tables

    @pytest.mark.parametrize(
        "index_name",
        [
            "ix_memories_surface_date",
            "ix_memories_status_surface",
            "ix_memories_surfaceable",
            "ix_memory_images_image_id",
        ],
    )
    def test_indexes_exist(self, test_db: str, index_name: str):
        conn = sqlite3.connect(test_db)
        names = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'index'"
            )
        }
        conn.close()
        assert index_name in names

    @pytest.mark.parametrize("event_type", ["holiday", "", "ANNIVERSARY"])
    def test_event_type_check_constraint_rejects_unknown_values(
        self, test_db: str, event_type: str
    ):
        with pytest.raises(sqlite3.IntegrityError):
            db_upsert_memory(make_memory("k", event_type=event_type), [])


# ##############################
# Upsert
# ##############################


class TestUpsertMemory:
    def test_inserts_memory_and_images(self, images: List[str]):
        memory = make_memory("anniv:07-26:2024")
        memory_id = db_upsert_memory(memory, entries(images[:3]))

        assert memory_id == memory["memory_id"]
        stored = db_get_memory(memory_id)
        assert stored["title"] == "2 years ago today"
        assert [img["id"] for img in db_get_memory_images(memory_id)] == images[:3]

    def test_requires_memory_id_and_dedupe_key(self, test_db: str):
        with pytest.raises(ValueError):
            db_upsert_memory({"dedupe_key": "k", "event_type": "anniversary"}, [])

    def test_conflict_keeps_the_original_memory_id(self, images: List[str]):
        first = db_upsert_memory(make_memory("anniv:07-26:2024"), entries(images[:2]))
        second = db_upsert_memory(make_memory("anniv:07-26:2024"), entries(images[:2]))

        assert second == first
        assert db_list_memories()[1] == 1

    def test_conflict_replaces_images_and_updates_fields(self, images: List[str]):
        memory_id = db_upsert_memory(
            make_memory("anniv:07-26:2024"), entries(images[:4])
        )
        db_upsert_memory(
            make_memory("anniv:07-26:2024", title="retitled", score=0.9),
            entries(images[4:]),
        )

        stored = db_get_memory(memory_id)
        assert stored["title"] == "retitled"
        assert stored["score"] == 0.9
        assert [img["id"] for img in db_get_memory_images(memory_id)] == images[4:]

    def test_conflict_preserves_user_state(self, images: List[str]):
        """Re-curation must not resurface a memory the user already dismissed."""
        memory_id = db_upsert_memory(
            make_memory("anniv:07-26:2024"), entries(images[:2])
        )
        db_mark_memory(memory_id, viewed=True, notified=True, dismissed=True)

        db_upsert_memory(
            make_memory("anniv:07-26:2024", title="regenerated"), entries(images[:3])
        )

        stored = db_get_memory(memory_id)
        assert stored["title"] == "regenerated"
        assert stored["viewed_at"] is not None
        assert stored["notified_at"] is not None
        assert stored["dismissed"] is True

    def test_signals_round_trip_as_json(self, images: List[str]):
        memory_id = db_upsert_memory(
            make_memory("k", signals={"favourite": 0.5, "gps_novelty": 0.1}),
            entries(images[:2]),
        )
        assert db_get_memory(memory_id)["signals"] == {
            "favourite": 0.5,
            "gps_novelty": 0.1,
        }

    def test_missing_signals_read_back_as_none(self, images: List[str]):
        memory_id = db_upsert_memory(make_memory("k"), entries(images[:2]))
        assert db_get_memory(memory_id)["signals"] is None


# ##############################
# Cascade behaviour
# ##############################


class TestCascades:
    def test_deleting_an_image_removes_its_memory_rows(self, images: List[str]):
        """Guards the FK pragma: a plain sqlite3.connect would skip this cascade."""
        memory_id = db_upsert_memory(make_memory("k"), entries(images[:3]))

        db_delete_images_by_ids([images[0]])

        remaining = [img["id"] for img in db_get_memory_images(memory_id)]
        assert remaining == images[1:3]

    def test_deleting_the_cover_image_nulls_the_reference(self, images: List[str]):
        memory_id = db_upsert_memory(
            make_memory("k", cover_image_id=images[0]), entries(images[:3])
        )

        db_delete_images_by_ids([images[0]])

        assert db_get_memory(memory_id)["cover_image_id"] is None

    def test_deleting_a_memory_removes_its_image_rows(self, images: List[str]):
        memory_id = db_upsert_memory(make_memory("k"), entries(images[:3]))

        assert db_delete_memory(memory_id) is True
        assert db_get_memory_images(memory_id) == []
        assert db_delete_memory(memory_id) is False

    def test_live_image_count_reflects_deletions(self, images: List[str]):
        memory_id = db_upsert_memory(
            make_memory("k", image_count=3), entries(images[:3])
        )

        db_delete_images_by_ids(images[:2])

        stored = db_get_memory(memory_id)
        # The stored count is a generation-time snapshot; the live count is not.
        assert stored["image_count"] == 3
        assert stored["live_image_count"] == 1


# ##############################
# Marking and pruning
# ##############################


class TestMarkAndPrune:
    @pytest.mark.parametrize(
        "kwargs, column",
        [
            ({"viewed": True}, "viewed_at"),
            ({"notified": True}, "notified_at"),
        ],
    )
    def test_marks_timestamps_independently(
        self, images: List[str], kwargs: Dict[str, bool], column: str
    ):
        memory_id = db_upsert_memory(make_memory("k"), entries(images[:2]))

        assert db_mark_memory(memory_id, **kwargs) is True

        stored = db_get_memory(memory_id)
        assert stored[column] is not None
        other = "notified_at" if column == "viewed_at" else "viewed_at"
        assert stored[other] is None

    def test_marking_false_clears_the_timestamp(self, images: List[str]):
        memory_id = db_upsert_memory(make_memory("k"), entries(images[:2]))
        db_mark_memory(memory_id, viewed=True)

        db_mark_memory(memory_id, viewed=False)

        assert db_get_memory(memory_id)["viewed_at"] is None

    def test_marking_nothing_is_a_noop(self, images: List[str]):
        memory_id = db_upsert_memory(make_memory("k"), entries(images[:2]))
        assert db_mark_memory(memory_id) is False

    def test_marking_an_unknown_memory_returns_false(self, test_db: str):
        assert db_mark_memory("missing", viewed=True) is False

    def test_prune_marks_shrunken_memories_empty(self, images: List[str]):
        keep = db_upsert_memory(make_memory("keep"), entries(images[:3]))
        shrink = db_upsert_memory(make_memory("shrink"), entries(images[3:]))

        db_delete_images_by_ids(images[3:])

        assert db_prune_empty_memories(2) == 1
        assert db_get_memory(shrink)["status"] == "empty"
        assert db_get_memory(keep)["status"] == "complete"


# ##############################
# Listing and surfacing
# ##############################


class TestListAndSurface:
    def test_list_excludes_dismissed_by_default(self, images: List[str]):
        db_upsert_memory(make_memory("a"), entries(images[:2]))
        dismissed = db_upsert_memory(make_memory("b"), entries(images[2:4]))
        db_mark_memory(dismissed, dismissed=True)

        assert db_list_memories()[1] == 1
        assert db_list_memories(include_dismissed=True)[1] == 2

    def test_list_can_exclude_viewed(self, images: List[str]):
        viewed = db_upsert_memory(make_memory("a"), entries(images[:2]))
        db_upsert_memory(make_memory("b"), entries(images[2:4]))
        db_mark_memory(viewed, viewed=True)

        assert db_list_memories(include_viewed=False)[1] == 1

    def test_list_filters_by_event_type(self, images: List[str]):
        db_upsert_memory(make_memory("a"), entries(images[:2]))
        db_upsert_memory(
            make_memory("b", event_type="import_event"), entries(images[2:4])
        )

        rows, total = db_list_memories(event_type="import_event")
        assert total == 1
        assert rows[0]["event_type"] == "import_event"

    def test_list_excludes_incomplete_memories(self, images: List[str]):
        db_upsert_memory(make_memory("a", status="pending"), entries(images[:2]))
        db_upsert_memory(make_memory("b", status="failed"), entries(images[2:4]))

        assert db_list_memories()[1] == 0

    def test_list_paginates_newest_first(self, images: List[str]):
        db_upsert_memory(make_memory("old", surface_date="2026-07-01"), [])
        db_upsert_memory(make_memory("new", surface_date="2026-07-20"), [])

        rows, total = db_list_memories(limit=1, offset=0)
        assert total == 2
        assert rows[0]["dedupe_key"] == "new"
        assert db_list_memories(limit=1, offset=1)[0][0]["dedupe_key"] == "old"

    def test_surfaceable_prefers_recent_then_highest_score(self, images: List[str]):
        db_upsert_memory(make_memory("older", surface_date="2026-07-01", score=0.9), [])
        db_upsert_memory(make_memory("low", surface_date="2026-07-20", score=0.2), [])
        db_upsert_memory(make_memory("high", surface_date="2026-07-20", score=0.8), [])

        assert db_get_surfaceable_memory("2026-07-26")["dedupe_key"] == "high"

    @pytest.mark.parametrize(
        "overrides, mark",
        [
            ({"status": "pending"}, None),
            ({"status": "empty"}, None),
            ({"surface_date": "2026-08-01"}, None),  # dated in the future
            ({}, "viewed"),
            ({}, "dismissed"),
        ],
    )
    def test_surfaceable_excludes_ineligible_memories(
        self, images: List[str], overrides: Dict[str, Any], mark: Optional[str]
    ):
        memory_id = db_upsert_memory(make_memory("k", **overrides), entries(images[:2]))
        if mark:
            db_mark_memory(memory_id, **{mark: True})

        assert db_get_surfaceable_memory("2026-07-26") is None

    def test_unviewed_count_tracks_marking(self, images: List[str]):
        first = db_upsert_memory(make_memory("a"), entries(images[:2]))
        db_upsert_memory(make_memory("b"), entries(images[2:4]))

        assert db_count_unviewed_memories("2026-07-26") == 2
        db_mark_memory(first, viewed=True)
        assert db_count_unviewed_memories("2026-07-26") == 1


# ##############################
# Dedupe keys and recent use
# ##############################


class TestDedupeAndRecentUse:
    def test_dedupe_key_is_unique_across_memories(self, images: List[str]):
        db_upsert_memory(make_memory("shared"), entries(images[:2]))
        db_upsert_memory(make_memory("shared"), entries(images[2:4]))

        assert db_list_memories()[1] == 1

    def test_existing_dedupe_keys_filter_by_signature(self, images: List[str]):
        db_upsert_memory(make_memory("a", params_signature="sig-1"), [])
        db_upsert_memory(make_memory("b", params_signature="sig-2"), [])

        assert db_get_existing_dedupe_keys() == {"a", "b"}
        assert db_get_existing_dedupe_keys("sig-1") == {"a"}
        assert db_get_existing_dedupe_keys("sig-3") == set()

    @pytest.mark.parametrize(
        "surface_date, expected",
        [
            ("2026-07-25", True),  # 1 day ago
            ("2026-06-27", True),  # 29 days ago
            ("2026-06-26", True),  # exactly 30 days ago, inclusive
            ("2026-06-25", False),  # 31 days ago
        ],
    )
    def test_recently_used_window_boundary(
        self, images: List[str], surface_date: str, expected: bool
    ):
        db_upsert_memory(
            make_memory("k", surface_date=surface_date), entries(images[:2])
        )

        used = db_get_recently_used_image_ids(30, "2026-07-26")
        assert (images[0] in used) is expected

    def test_recently_used_is_empty_without_memories(self, images: List[str]):
        assert db_get_recently_used_image_ids(30, "2026-07-26") == set()


# ##############################
# Anniversary candidates
# ##############################


class TestAnniversaryCandidates:
    def test_matches_requested_month_days_only(self, images: List[str]):
        rows = db_get_anniversary_candidates(["06-15"], 2025)
        assert {row["id"] for row in rows} == set(images)

        assert db_get_anniversary_candidates(["06-16"], 2025) == []

    def test_excludes_years_after_the_cutoff(self, images: List[str]):
        assert db_get_anniversary_candidates(["06-15"], 2023) == []

    def test_returns_capture_year_and_empty_for_no_month_days(self, images: List[str]):
        rows = db_get_anniversary_candidates(["06-15"], 2025)
        assert rows[0]["capture_year"] == 2024
        assert db_get_anniversary_candidates([], 2025) == []


# ##############################
# Runs
# ##############################


class TestMemoryRuns:
    def test_start_then_finish_a_run(self, test_db: str):
        db_start_memory_run("2026-07-26", "sig-1")
        assert db_get_memory_run("2026-07-26")["status"] == "running"

        db_finish_memory_run("2026-07-26", "complete", 3)

        run = db_get_memory_run("2026-07-26")
        assert run["status"] == "complete"
        assert run["generated_count"] == 3
        assert run["finished_at"] is not None

    def test_restarting_a_run_clears_the_previous_outcome(self, test_db: str):
        db_start_memory_run("2026-07-26", "sig-1")
        db_finish_memory_run("2026-07-26", "failed", 0, "boom")

        db_start_memory_run("2026-07-26", "sig-2")

        run = db_get_memory_run("2026-07-26")
        assert run["status"] == "running"
        assert run["error"] is None
        assert run["generated_count"] == 0
        assert run["params_signature"] == "sig-2"

    def test_unknown_run_date_returns_none(self, test_db: str):
        assert db_get_memory_run("2026-01-01") is None

    @pytest.mark.parametrize("status", ["running", "queued", ""])
    def test_finish_rejects_non_terminal_status(self, test_db: str, status: str):
        db_start_memory_run("2026-07-26", "sig-1")
        with pytest.raises(ValueError):
            db_finish_memory_run("2026-07-26", status)

    def test_reap_fails_runs_past_the_staleness_window(self, test_db: str):
        db_start_memory_run("2026-07-26", "sig-1")
        set_started_at(test_db, "2026-07-26", "datetime('now', '-31 minutes')")

        assert db_reap_stale_memory_runs(30) == 1

        run = db_get_memory_run("2026-07-26")
        assert run["status"] == "failed"
        assert "Interrupted" in run["error"]

    def test_reap_leaves_fresh_runs_alone(self, test_db: str):
        db_start_memory_run("2026-07-26", "sig-1")
        set_started_at(test_db, "2026-07-26", "datetime('now', '-29 minutes')")

        assert db_reap_stale_memory_runs(30) == 0
        assert db_get_memory_run("2026-07-26")["status"] == "running"

    def test_reap_ignores_finished_runs(self, test_db: str):
        db_start_memory_run("2026-07-26", "sig-1")
        db_finish_memory_run("2026-07-26", "complete", 1)
        set_started_at(test_db, "2026-07-26", "datetime('now', '-99 minutes')")

        assert db_reap_stale_memory_runs(30) == 0


# ##############################
# Indexing gate
# ##############################


class TestIndexingBusy:
    @pytest.mark.parametrize(
        "indexing_status, ai_tagging, tagging_completed, expected",
        [
            ("completed", 1, 1, False),
            ("not_started", 0, 0, False),  # tagging off: nothing pending
            ("in_progress", 0, 0, True),
            ("completed", 1, 0, True),  # tagging enabled but unfinished
            ("completed", 1, None, True),  # NULL counts as unfinished
            ("in_progress", 1, 1, True),
        ],
    )
    def test_reports_busy_for_indexing_or_pending_tagging(
        self,
        test_db: str,
        indexing_status: str,
        ai_tagging: int,
        tagging_completed: Optional[int],
        expected: bool,
    ):
        conn = sqlite3.connect(test_db)
        conn.execute(
            "INSERT INTO folders (folder_id, folder_path, last_modified_time, "
            "AI_Tagging, taggingCompleted, indexing_status) VALUES (?, ?, 0, ?, ?, ?)",
            ("f-1", "/photos", ai_tagging, tagging_completed, indexing_status),
        )
        conn.commit()
        conn.close()

        assert db_is_indexing_busy() is expected

    def test_no_folders_is_not_busy(self, test_db: str):
        assert db_is_indexing_busy() is False
