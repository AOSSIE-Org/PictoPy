"""
The export pass end to end: real PNG files indexed the way the app indexes
them, real database writes, and the file system checked afterwards.
"""

import json
import os
from pathlib import Path
from typing import Dict, Iterator, List

import numpy as np
import pytest
from PIL import Image

import app.utils.xmp.exporter as exporter
from app.database.albums import db_create_album_with_images, db_update_album
from app.database.face_clusters import db_insert_clusters_batch, db_update_cluster
from app.database.faces import db_insert_face_embeddings
from app.database.image_embeddings import db_upsert_image_embeddings
from app.database.images import (
    db_bulk_insert_images,
    db_get_image_sync_state_by_folder_ids,
    db_insert_image_classes_batch,
    db_toggle_image_favourite_status,
)
from app.database.metadata import db_update_metadata
from app.database.xmp_export_state import db_get_xmp_export_counts
from app.utils.images import image_util_extract_metadata, image_util_is_unchanged
from app.utils.xmp import PictoPyMetadata, read_image_metadata
from app.utils.xmp.containers.png import PngContainer
from app.utils.xmp.exporter import (
    xmp_export_if_enabled,
    xmp_export_run,
)
from tests.test_xmp_export_state import _create_schema, _sql
from tests.test_xmp_export_state import db_path as db_path  # noqa: F401 (fixture)

FOLDER = 7


def make_library(database: str, folder: Path) -> Path:
    """Full schema plus one indexed folder; shared with the route tests."""
    _create_schema()
    _sql(
        database,
        "INSERT INTO folders (folder_id, folder_path) VALUES (?, ?)",
        (FOLDER, str(folder)),
    )
    return folder


@pytest.fixture
def library(db_path: str, tmp_path: Path) -> Iterator[Path]:  # noqa: F811
    yield make_library(db_path, tmp_path)


def _photo(folder: Path, image_id: str, ext: str = "png") -> str:
    """A real image file, indexed with the app's own metadata extractor."""
    path = folder / f"{image_id}.{ext}"
    rng = np.random.default_rng(abs(hash(image_id)) % 2**32)
    Image.fromarray(rng.integers(0, 256, (24, 32, 3), dtype=np.uint8)).save(path)
    # A year-old mtime, as a real library has; export must keep it.
    os.utime(path, ns=(1_700_000_000_000_000_000, 1_700_000_000_000_000_000))
    thumb = folder / f"{image_id}_thumb.jpg"
    thumb.write_bytes(b"thumbnail")
    assert db_bulk_insert_images(
        [
            {
                "id": image_id,
                "path": str(path),
                "folder_id": FOLDER,
                "thumbnailPath": str(thumb),
                "metadata": json.dumps(image_util_extract_metadata(str(path))),
                "isTagged": True,
                "isEmbedded": False,
                "latitude": None,
                "longitude": None,
                "captured_at": None,
            }
        ]
    )
    return str(path)


def _tag(image_id: str) -> None:
    db_insert_image_classes_batch([(image_id, 0)])  # "person"


def _files(paths: List[str]) -> Dict[str, tuple]:
    return {p: (Path(p).read_bytes(), os.stat(p).st_mtime_ns) for p in paths}


def _pending() -> int:
    return db_get_xmp_export_counts()["pending"]


def _enable(on: bool = True) -> None:
    assert db_update_metadata({"user_preferences": {"Metadata_Export": on}})


class TestExportPass:
    def test_writes_tagged_photos_and_keeps_their_dates(self, library):
        path = _photo(library, "a")
        _tag("a")
        mtime = os.stat(path).st_mtime_ns

        summary = xmp_export_run()
        assert summary["written"] == 1
        stored = read_image_metadata(path)
        assert stored is not None and stored.tags == ["person"]
        assert os.stat(path).st_mtime_ns == mtime
        assert _pending() == 0

    def test_rescan_skips_the_file_it_just_wrote(self, library):
        """Export changes the file's size; the stored stat must follow it, or
        the folder rescan would treat every exported photo as edited."""
        path = _photo(library, "a")
        _tag("a")
        xmp_export_run()
        recorded = db_get_image_sync_state_by_folder_ids([FOLDER])
        assert image_util_is_unchanged(path, recorded[os.path.normcase(path)])

    def test_second_pass_touches_no_files(self, library, monkeypatch):
        paths = [_photo(library, i) for i in ("a", "b")]
        _tag("a")
        _tag("b")
        xmp_export_run()
        before = _files(paths)

        def must_not_write(*args, **kwargs):  # type: ignore[no-untyped-def]
            raise AssertionError("nothing changed, so no file may be opened")

        monkeypatch.setattr(exporter, "write_image_metadata", must_not_write)
        assert xmp_export_run()["written"] == 0
        assert _files(paths) == before

    def test_a_change_that_cancels_out_touches_no_file(self, library, monkeypatch):
        """Marked dirty, but the data is what the file already holds: the
        stored digest settles it without opening the file."""
        path = _photo(library, "a")
        _tag("a")
        xmp_export_run()
        db_toggle_image_favourite_status("a")
        db_toggle_image_favourite_status("a")
        assert _pending() == 1
        before = _files([path])

        def must_not_write(*args, **kwargs):  # type: ignore[no-untyped-def]
            raise AssertionError("the digest already matches; no file access")

        monkeypatch.setattr(exporter, "write_image_metadata", must_not_write)
        summary = xmp_export_run()
        assert (summary["unchanged"], summary["failed"]) == (1, 0)
        assert _files([path]) == before
        assert _pending() == 0

    def test_only_edited_photos_are_rewritten(self, library):
        paths = {i: _photo(library, i) for i in ("a", "b", "c")}
        for i in paths:
            _tag(i)
        xmp_export_run()
        before = _files(list(paths.values()))

        db_toggle_image_favourite_status("b")
        summary = xmp_export_run()
        assert summary["written"] == 1
        after = _files(list(paths.values()))
        assert after[paths["a"]] == before[paths["a"]]
        assert after[paths["c"]] == before[paths["c"]]
        assert after[paths["b"]] != before[paths["b"]]
        stored = read_image_metadata(paths["b"])
        assert stored is not None and stored.favourite is True

    def test_nothing_to_store_means_the_file_is_never_touched(self, library):
        path = _photo(library, "a")  # untagged, not favourited, in no album
        before = _files([path])
        summary = xmp_export_run()
        assert summary["skipped"] == 1 and summary["written"] == 0
        assert _files([path]) == before
        assert _pending() == 0

    def test_data_that_disappears_is_cleared_from_the_file(self, library):
        path = _photo(library, "a")
        db_toggle_image_favourite_status("a")
        xmp_export_run()
        stored = read_image_metadata(path)
        assert stored is not None and stored.favourite is True

        db_toggle_image_favourite_status("a")  # back to nothing worth storing
        assert xmp_export_run()["written"] == 1
        stored = read_image_metadata(path)
        assert stored is not None and stored.favourite is False

    def test_other_formats_are_never_touched(self, library):
        jpg = _photo(library, "j", ext="jpg")
        _tag("j")
        before = _files([jpg])
        assert xmp_export_run()["checked"] == 0
        assert _files([jpg]) == before

    def test_locked_album_names_never_reach_the_file(self, library):
        path = _photo(library, "a")
        db_create_album_with_images("al", "Secret trip", "", ["a"])
        xmp_export_run()
        assert b"Secret trip" in Path(path).read_bytes()

        db_update_album("al", "Secret trip", "", True, "pw")
        xmp_export_run()
        assert b"Secret trip" not in Path(path).read_bytes()

    def test_person_rename_reaches_every_photo_of_them(self, library):
        paths = [_photo(library, i) for i in ("a", "b")]
        db_insert_clusters_batch(
            [{"cluster_id": "c1", "cluster_name": "Ann", "face_image_base64": None}]
        )
        for i in ("a", "b"):
            db_insert_face_embeddings(i, np.full(4, 0.5, np.float32), cluster_id="c1")
        xmp_export_run()

        db_update_cluster("c1", "Annabel")
        assert xmp_export_run()["written"] == 2
        for path in paths:
            stored = read_image_metadata(path)
            assert stored is not None and stored.faces[0].cluster_name == "Annabel"

    def test_embeddings_are_written(self, library):
        path = _photo(library, "a")
        db_upsert_image_embeddings(
            [("a", "siglip2-base", np.full(8, 0.25, np.float32))]
        )
        xmp_export_run()
        stored = read_image_metadata(path)
        assert stored is not None and stored.image_embedding is not None
        assert stored.image_embedding.model_version == "siglip2-base"

    def test_batches_cover_the_whole_library(self, library, monkeypatch):
        monkeypatch.setattr(exporter, "EXPORT_BATCH_SIZE", 2)
        ids = [f"i{n}" for n in range(5)]
        for i in ids:
            _photo(library, i)
            _tag(i)
        assert xmp_export_run()["written"] == 5
        assert _pending() == 0


class TestChangesAndFailures:
    def test_edit_during_the_write_keeps_the_photo_pending(self, library, monkeypatch):
        path = _photo(library, "a")
        _tag("a")
        real_write = exporter.write_image_metadata

        def favourite_lands_mid_write(p, metadata):  # type: ignore[no-untyped-def]
            db_toggle_image_favourite_status("a")
            return real_write(p, metadata)

        monkeypatch.setattr(exporter, "write_image_metadata", favourite_lands_mid_write)
        xmp_export_run()
        assert _pending() == 1  # the file holds the pre-favourite data

        monkeypatch.setattr(exporter, "write_image_metadata", real_write)
        xmp_export_run()
        stored = read_image_metadata(path)
        assert stored is not None and stored.favourite is True
        assert _pending() == 0

    def test_a_failing_file_does_not_stop_the_others(self, library, monkeypatch):
        good = _photo(library, "a")
        bad = _photo(library, "b")
        _tag("a")
        _tag("b")
        real_write = exporter.write_image_metadata

        def locked(p, metadata):  # type: ignore[no-untyped-def]
            if p == bad:
                raise PermissionError("file is open in another program")
            return real_write(p, metadata)

        monkeypatch.setattr(exporter, "write_image_metadata", locked)
        summary = xmp_export_run()
        assert (summary["written"], summary["failed"]) == (1, 1)
        assert read_image_metadata(good) is not None
        counts = db_get_xmp_export_counts()
        assert (counts["pending"], counts["failed"]) == (1, 1)

        # The lock is released: the next pass retries and succeeds.
        monkeypatch.setattr(exporter, "write_image_metadata", real_write)
        assert xmp_export_run()["written"] == 1
        assert db_get_xmp_export_counts()["failed"] == 0

    def test_missing_file_is_a_failure_not_a_crash(self, library):
        path = _photo(library, "a")
        _tag("a")
        moved = path + ".unplugged"
        os.rename(path, moved)  # an external drive that isn't connected
        summary = xmp_export_run()
        assert summary["failed"] == 1
        assert _pending() == 1

        os.rename(moved, path)  # plugged back in: the next pass catches up
        assert xmp_export_run()["written"] == 1
        assert _pending() == 0

    def test_unreadable_existing_xmp_is_left_alone(self, library):
        path = _photo(library, "a")
        _tag("a")
        PngContainer().write_xmp(path, b"<broken xmp")
        before = _files([path])
        summary = xmp_export_run()
        assert summary["skipped"] == 1
        assert _files([path]) == before
        assert db_get_xmp_export_counts()["skipped"] == 1
        # Automatic passes don't keep retrying a file they must not touch.
        assert xmp_export_run()["checked"] == 0


class TestManualRun:
    def test_rechecks_a_file_another_tool_changed(self, library):
        path = _photo(library, "a")
        _tag("a")
        xmp_export_run()
        # Another tool rewrites the file and drops our metadata.
        Image.open(path).save(path)
        assert read_image_metadata(path) is None

        assert xmp_export_run()["written"] == 0  # automatic: DB unchanged
        assert xmp_export_run(include_clean=True)["written"] == 1
        stored = read_image_metadata(path)
        assert stored is not None and stored.tags == ["person"]

    def test_unchanged_library_is_not_reread(self, library, monkeypatch):
        _photo(library, "a")
        _tag("a")
        xmp_export_run()
        monkeypatch.setattr(
            exporter,
            "collect_image_metadata",
            lambda ids: pytest.fail("clean images with untouched files need no data"),
        )
        assert xmp_export_run(include_clean=True)["unchanged"] == 1


class TestToggle:
    def test_off_by_default_and_writes_nothing(self, library):
        path = _photo(library, "a")
        _tag("a")
        before = _files([path])
        assert xmp_export_if_enabled() is None
        assert _files([path]) == before

    def test_on_writes(self, library):
        path = _photo(library, "a")
        _tag("a")
        _enable()
        summary = xmp_export_if_enabled()
        assert summary is not None and summary["written"] == 1
        assert read_image_metadata(path) is not None

    def test_corrupt_preferences_count_as_off(self, library):
        _photo(library, "a")
        _tag("a")
        assert db_update_metadata({"user_preferences": {"Metadata_Export": "maybe"}})
        assert xmp_export_if_enabled() is None


def test_exported_metadata_round_trips_the_database(library):
    """What lands in the file is what the database holds."""
    path = _photo(library, "a")
    _tag("a")
    db_toggle_image_favourite_status("a")
    xmp_export_run()
    stored = read_image_metadata(path)
    assert isinstance(stored, PictoPyMetadata)
    assert (stored.tags, stored.favourite) == (["person"], True)
