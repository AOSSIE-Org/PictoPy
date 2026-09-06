"""
The watcher treats any file change as a user edit, so a write of PictoPy's own
would come back as a folder resync. These cover the ledger that tells them
apart, and the atomic replace that populates it.
"""

import os
import sqlite3
import tempfile
import time
from typing import Iterator

import pytest

from app.database.self_writes import (
    SELF_WRITE_TTL_SECONDS,
    db_create_self_writes_table,
    db_record_self_write,
    db_take_matching_self_writes,
    self_write_key,
)
from app.utils.self_write import SELF_WRITE_TEMP_PREFIX, self_write_util_replace


@pytest.fixture(scope="function")
def test_db(monkeypatch: pytest.MonkeyPatch) -> Iterator[str]:
    db_fd, db_path = tempfile.mkstemp()
    os.close(db_fd)

    monkeypatch.setattr("app.config.settings.DATABASE_PATH", db_path)
    monkeypatch.setattr("app.database.self_writes.DATABASE_PATH", db_path)
    db_create_self_writes_table()

    yield db_path

    os.unlink(db_path)


def _observe(path: str):
    stats = os.stat(path)
    return (path, stats.st_size, int(stats.st_mtime))


class TestLedger:
    def test_a_recorded_write_is_claimed(self, test_db, tmp_path):
        photo = tmp_path / "a.jpg"
        photo.write_bytes(b"x" * 100)
        path, size, mtime = _observe(str(photo))

        db_record_self_write(path, size, mtime)

        assert db_take_matching_self_writes([(path, size, mtime)]) == {path}

    def test_an_unrecorded_file_is_left_alone(self, test_db, tmp_path):
        photo = tmp_path / "a.jpg"
        photo.write_bytes(b"x" * 100)
        assert db_take_matching_self_writes([_observe(str(photo))]) == set()

    def test_a_later_edit_to_the_same_path_is_not_claimed(self, test_db, tmp_path):
        """The user changing the file we wrote is a real change, not our echo."""
        photo = tmp_path / "a.jpg"
        photo.write_bytes(b"x" * 100)
        path, size, mtime = _observe(str(photo))
        db_record_self_write(path, size, mtime)

        photo.write_bytes(b"y" * 4096)

        assert db_take_matching_self_writes([_observe(str(photo))]) == set()

    def test_an_entry_is_claimed_only_once(self, test_db, tmp_path):
        """A second event for one write must read as a real change."""
        photo = tmp_path / "a.jpg"
        photo.write_bytes(b"x" * 100)
        observed = _observe(str(photo))
        db_record_self_write(*observed)

        assert db_take_matching_self_writes([observed]) == {observed[0]}
        assert db_take_matching_self_writes([observed]) == set()

    def test_claiming_one_path_leaves_the_others(self, test_db, tmp_path):
        ours = tmp_path / "ours.jpg"
        theirs = tmp_path / "theirs.jpg"
        ours.write_bytes(b"x" * 100)
        theirs.write_bytes(b"y" * 100)
        db_record_self_write(*_observe(str(ours)))

        matched = db_take_matching_self_writes(
            [_observe(str(ours)), _observe(str(theirs))]
        )

        assert matched == {str(ours)}

    def test_lookup_survives_a_differently_spelled_path(
        self, test_db, tmp_path, monkeypatch
    ):
        """
        The watcher reports whatever the OS hands it, so the two sides agree on a
        normalised key rather than on the exact string. Case folding is part of
        that on Windows but not on Linux, where paths really are case-sensitive;
        absolute-vs-relative is the part that holds everywhere.
        """
        photo = tmp_path / "a.jpg"
        photo.write_bytes(b"x" * 100)
        _, size, mtime = _observe(str(photo))
        db_record_self_write(str(photo), size, mtime)

        monkeypatch.chdir(tmp_path)

        assert db_take_matching_self_writes([("a.jpg", size, mtime)]) == {"a.jpg"}

    def test_nothing_observed_queries_nothing(self, test_db):
        assert db_take_matching_self_writes([]) == set()

    def test_stale_entries_are_pruned_on_the_next_write(self, test_db, tmp_path):
        """An entry the watcher never claimed was one it missed; it must not linger."""
        photo = tmp_path / "a.jpg"
        photo.write_bytes(b"x" * 100)
        path, size, mtime = _observe(str(photo))
        db_record_self_write(path, size, mtime)

        conn = sqlite3.connect(test_db)
        conn.execute(
            "UPDATE self_writes SET written_at = ?",
            (int(time.time()) - SELF_WRITE_TTL_SECONDS - 60,),
        )
        conn.commit()
        conn.close()

        db_record_self_write(str(tmp_path / "unrelated.jpg"), 1, 1)

        assert db_take_matching_self_writes([(path, size, mtime)]) == set()

    def test_an_unreadable_ledger_suppresses_nothing(self, test_db, tmp_path):
        """Failing open costs a rescan; failing closed would drop a real change."""
        photo = tmp_path / "a.jpg"
        photo.write_bytes(b"x" * 100)
        observed = _observe(str(photo))
        db_record_self_write(*observed)

        conn = sqlite3.connect(test_db)
        conn.execute("DROP TABLE self_writes")
        conn.commit()
        conn.close()

        assert db_take_matching_self_writes([observed]) == set()


class TestAtomicReplace:
    def test_the_new_bytes_land(self, test_db, tmp_path):
        photo = tmp_path / "a.jpg"
        photo.write_bytes(b"original")

        assert self_write_util_replace(str(photo), b"replaced") is True
        assert photo.read_bytes() == b"replaced"

    def test_the_write_is_recorded_so_the_watcher_ignores_it(self, test_db, tmp_path):
        photo = tmp_path / "a.jpg"
        photo.write_bytes(b"original")

        self_write_util_replace(str(photo), b"replaced")

        assert db_take_matching_self_writes([_observe(str(photo))]) == {str(photo)}

    def test_the_ledger_is_written_before_the_bytes_are_visible(
        self, test_db, tmp_path, monkeypatch
    ):
        """
        The watcher can fire the instant the rename lands, so recording after it
        would leave a window where our own write reads as a user edit.
        """
        photo = tmp_path / "a.jpg"
        photo.write_bytes(b"original")

        def explode(src, dst):
            raise OSError("rename interrupted")

        monkeypatch.setattr("app.utils.self_write.os.replace", explode)

        assert self_write_util_replace(str(photo), b"replaced") is False

        conn = sqlite3.connect(test_db)
        rows = conn.execute("SELECT path FROM self_writes").fetchall()
        conn.close()
        assert rows == [(self_write_key(str(photo)),)]

    def test_a_failed_replace_leaves_the_original_and_no_scratch_file(
        self, test_db, tmp_path, monkeypatch
    ):
        photo = tmp_path / "a.jpg"
        photo.write_bytes(b"original")

        def explode(src, dst):
            raise OSError("rename interrupted")

        monkeypatch.setattr("app.utils.self_write.os.replace", explode)
        self_write_util_replace(str(photo), b"replaced")

        assert photo.read_bytes() == b"original"
        assert [p.name for p in tmp_path.iterdir()] == ["a.jpg"]

    def test_an_unwritable_location_reports_failure(self, test_db, tmp_path):
        missing = tmp_path / "no-such-dir" / "a.jpg"
        assert self_write_util_replace(str(missing), b"data") is False

    def test_success_leaves_no_scratch_file_behind(self, test_db, tmp_path):
        photo = tmp_path / "a.jpg"
        photo.write_bytes(b"original")

        self_write_util_replace(str(photo), b"replaced")

        leftovers = [
            p.name
            for p in tmp_path.iterdir()
            if p.name.startswith(SELF_WRITE_TEMP_PREFIX)
        ]
        assert leftovers == []
