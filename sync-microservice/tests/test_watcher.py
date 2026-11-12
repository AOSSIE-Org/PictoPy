import os
import shutil
from typing import List, Tuple

import pytest
from watchfiles import Change

from app.utils import watcher


@pytest.fixture
def api_calls(monkeypatch) -> List[Tuple[str, object]]:
    """Record the backend calls the watcher makes, in order, instead of sending them."""
    calls: List[Tuple[str, object]] = []
    monkeypatch.setattr(
        watcher,
        "watcher_util_call_sync_folder_api",
        lambda folder_id, folder_path: calls.append(("sync", folder_id)),
    )
    monkeypatch.setattr(
        watcher,
        "watcher_util_call_delete_folders_api",
        lambda folder_ids: calls.append(("delete", folder_ids)),
    )
    monkeypatch.setattr(watcher, "watcher_util_restart_folder_watcher", lambda: True)
    return calls


class _InOrder(set):
    """A change set that iterates in a fixed order, unlike the one watchfiles gives."""

    def __init__(self, changes: List[Tuple[Change, str]]):
        super().__init__(changes)
        self._order = list(changes)

    def __iter__(self):
        return iter(self._order)


def _watch(monkeypatch, folders: List[Tuple[str, str]]) -> None:
    for _, folder_path in folders:
        os.makedirs(folder_path, exist_ok=True)
    monkeypatch.setattr(watcher, "watched_folders", folders)


class TestWatcherFolderChanges:
    def test_renamed_subfolder_is_synced_through_its_parent(
        self, monkeypatch, api_calls, tmp_path
    ):
        photos = str(tmp_path / "Photos")
        trip = os.path.join(photos, "Trip")
        _watch(monkeypatch, [("root-id", photos), ("trip-id", trip)])

        renamed = os.path.join(photos, "Goa Trip 2026")
        os.rename(trip, renamed)
        watcher.watcher_util_handle_file_changes(
            {(Change.deleted, trip), (Change.added, renamed)}
        )

        # Deleting by id would cascade away the photos the parent's sync can
        # still recognise under the new name.
        assert api_calls == [("sync", "root-id")]

    def test_move_syncs_the_destination_before_the_source(
        self, monkeypatch, api_calls, tmp_path
    ):
        photos = str(tmp_path / "Photos")
        source = os.path.join(photos, "2024")
        destination = os.path.join(photos, "2025")
        trip = os.path.join(source, "Trip")
        _watch(
            monkeypatch,
            [
                ("root-id", photos),
                ("2024-id", source),
                ("2025-id", destination),
                ("trip-id", trip),
            ],
        )

        moved = os.path.join(destination, "Trip")
        shutil.move(trip, moved)
        watcher.watcher_util_handle_file_changes(
            {(Change.deleted, trip), (Change.added, moved)}
        )

        assert api_calls == [("sync", "2025-id"), ("sync", "2024-id")]

    def test_nested_deletion_is_synced_through_the_surviving_ancestor(
        self, monkeypatch, api_calls, tmp_path
    ):
        photos = str(tmp_path / "Photos")
        trip = os.path.join(photos, "Trip")
        day_one = os.path.join(trip, "Day 1")
        _watch(
            monkeypatch,
            [("root-id", photos), ("trip-id", trip), ("day-id", day_one)],
        )

        shutil.rmtree(trip)
        watcher.watcher_util_handle_file_changes(
            {(Change.deleted, trip), (Change.deleted, day_one)}
        )

        assert api_calls == [("sync", "root-id")]

    @pytest.mark.parametrize("deletion_first", [True, False])
    def test_moved_photo_syncs_the_destination_before_the_source(
        self, monkeypatch, api_calls, tmp_path, deletion_first
    ):
        photos = str(tmp_path / "Photos")
        source = os.path.join(photos, "2024")
        destination = os.path.join(photos, "2025")
        _watch(
            monkeypatch,
            [("root-id", photos), ("2024-id", source), ("2025-id", destination)],
        )
        old = os.path.join(source, "beach.jpg")
        new = os.path.join(destination, "beach.jpg")
        with open(new, "wb") as f:
            f.write(b"photo")

        changes = [(Change.deleted, old), (Change.added, new)]
        if not deletion_first:
            changes.reverse()
        watcher.watcher_util_handle_file_changes(_InOrder(changes))

        assert api_calls == [("sync", "2025-id"), ("sync", "2024-id")]

    @pytest.mark.parametrize("addition_first", [True, False])
    def test_source_that_also_gained_a_file_is_still_synced_last(
        self, monkeypatch, api_calls, tmp_path, addition_first
    ):
        photos = str(tmp_path / "Photos")
        source = os.path.join(photos, "2024")
        destination = os.path.join(photos, "2025")
        trip = os.path.join(source, "Trip")
        _watch(
            monkeypatch,
            [
                ("root-id", photos),
                ("2024-id", source),
                ("2025-id", destination),
                ("trip-id", trip),
            ],
        )
        moved = os.path.join(destination, "Trip")
        shutil.move(trip, moved)
        unrelated = os.path.join(source, "new.jpg")
        with open(unrelated, "wb") as f:
            f.write(b"photo")

        changes = [
            (Change.added, unrelated),
            (Change.deleted, trip),
            (Change.added, moved),
        ]
        if not addition_first:
            changes.reverse()
        watcher.watcher_util_handle_file_changes(_InOrder(changes))

        assert api_calls == [("sync", "2025-id"), ("sync", "2024-id")]

    @pytest.mark.parametrize("other_deletion_first", [True, False])
    def test_destination_that_also_lost_a_file_is_synced_before_the_source(
        self, monkeypatch, api_calls, tmp_path, other_deletion_first
    ):
        photos = str(tmp_path / "Photos")
        source = os.path.join(photos, "2024")
        destination = os.path.join(photos, "2025")
        _watch(
            monkeypatch,
            [("root-id", photos), ("2024-id", source), ("2025-id", destination)],
        )
        old = os.path.join(source, "beach.jpg")
        new = os.path.join(destination, "beach.jpg")
        with open(new, "wb") as f:
            f.write(b"photo")

        changes = [
            (Change.deleted, os.path.join(destination, "old.jpg")),
            (Change.deleted, old),
            (Change.added, new),
        ]
        if not other_deletion_first:
            changes = [changes[1], changes[2], changes[0]]
        watcher.watcher_util_handle_file_changes(_InOrder(changes))

        assert api_calls == [("sync", "2025-id"), ("sync", "2024-id")]

    def test_removed_library_folder_is_still_deleted(
        self, monkeypatch, api_calls, tmp_path
    ):
        photos = str(tmp_path / "Photos")
        _watch(monkeypatch, [("root-id", photos)])

        shutil.rmtree(photos)
        watcher.watcher_util_handle_file_changes({(Change.deleted, photos)})

        assert api_calls == [("delete", ["root-id"])]
