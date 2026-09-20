import sqlite3
from unittest.mock import patch

import pytest

from app.utils.albums import (
    AlbumFromMemoryResult,
    AlbumNameTakenError,
    album_util_create_from_memory,
)


class TestAlbumFromMemoryRace:
    """
    The name check is not atomic, so the insert can still hit the UNIQUE
    constraint. These cover the branch that decides what that meant.
    """

    def run_with_integrity_error(
        self, name_taken_on_recheck: bool
    ) -> AlbumFromMemoryResult:
        with patch("app.utils.albums.db_get_memory") as mock_get_memory, patch(
            "app.utils.albums.db_get_memory_images"
        ) as mock_get_images, patch(
            "app.utils.albums.db_get_album_by_name"
        ) as mock_get_by_name, patch(
            "app.utils.albums.db_create_album_with_images"
        ) as mock_create:
            mock_get_memory.return_value = {"memory_id": "mem-1", "subtitle": "July"}
            mock_get_images.return_value = [{"id": "img-1"}]
            # Free when first checked, then possibly taken by the time it fails.
            recheck = {"album_id": "other"} if name_taken_on_recheck else None
            mock_get_by_name.side_effect = [None, recheck]
            mock_create.side_effect = sqlite3.IntegrityError("UNIQUE constraint failed")

            return album_util_create_from_memory("mem-1", "Paris 2022")

    def test_a_name_taken_mid_request_reads_as_a_conflict(self) -> None:
        with pytest.raises(AlbumNameTakenError):
            self.run_with_integrity_error(name_taken_on_recheck=True)

    def test_any_other_integrity_error_is_not_swallowed(self) -> None:
        """A vanished image must not be reported as a duplicate name."""
        with pytest.raises(sqlite3.IntegrityError):
            self.run_with_integrity_error(name_taken_on_recheck=False)
