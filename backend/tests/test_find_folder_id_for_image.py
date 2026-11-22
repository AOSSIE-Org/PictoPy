"""
Tests for image_util_find_folder_id_for_image(), which walks up from an image's
folder to the nearest tracked folder.
"""

import os
import threading

from app.utils.images import image_util_find_folder_id_for_image

ROOT = os.path.abspath(os.sep)
TRACKED = os.path.join(ROOT, "photos")


def _find_with_timeout(
    image_path: str, folder_path_to_id: dict[str, str], timeout: float = 2.0
) -> str | None:
    # Run in a thread so a regression to the infinite loop fails instead of hanging pytest.
    result: dict[str, str | None] = {}

    def target() -> None:
        result["value"] = image_util_find_folder_id_for_image(
            image_path, folder_path_to_id
        )

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    thread.join(timeout)
    assert not thread.is_alive(), "lookup did not terminate"
    return result["value"]


def test_image_directly_in_tracked_folder() -> None:
    image = os.path.join(TRACKED, "a.jpg")
    assert _find_with_timeout(image, {TRACKED: "f1"}) == "f1"


def test_image_in_nested_subfolder_resolves_to_ancestor() -> None:
    image = os.path.join(TRACKED, "2024", "trip", "a.jpg")
    assert _find_with_timeout(image, {TRACKED: "f1"}) == "f1"


def test_most_specific_tracked_folder_wins() -> None:
    nested = os.path.join(TRACKED, "2024")
    image = os.path.join(nested, "a.jpg")
    assert _find_with_timeout(image, {TRACKED: "f1", nested: "f2"}) == "f2"


def test_untracked_image_stops_at_root() -> None:
    image = os.path.join(ROOT, "elsewhere", "deep", "a.jpg")
    assert _find_with_timeout(image, {TRACKED: "f1"}) is None


def test_image_at_root_with_no_tracked_folders() -> None:
    image = os.path.join(ROOT, "a.jpg")
    assert _find_with_timeout(image, {}) is None


def test_relative_path_without_match_returns_none() -> None:
    assert _find_with_timeout(os.path.join("a", "b.jpg"), {TRACKED: "f1"}) is None
