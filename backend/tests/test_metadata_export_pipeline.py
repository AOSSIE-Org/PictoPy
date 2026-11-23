"""
Where export sits in the processing pipeline: once per sequence, after every
photo stage, before the videos; and a failing export must not break anything.
"""

from typing import Callable, List

import pytest

import app.routes.folders as folders
import app.utils.xmp.exporter as exporter
from app.routes.models import submit_embedding_backfill_if_semantic

PHOTO_STAGES = [
    "image_util_process_untagged_images",
    "cluster_util_face_clusters_sync",
    "image_util_process_unembedded_images",
    "semantic_util_score_images",
    "_curate_memories",
]
VIDEO_STAGES = [
    "video_util_process_untagged_videos",
    "video_util_backfill_video_faces",
    "cluster_util_attach_keyframe_faces",
    "video_util_process_unembedded_frames",
    "semantic_util_score_videos",
]
OTHER = [
    "db_set_tagging_completed",
    "ensure_ai_tagging_models",
    "image_util_process_folder_images",
    "video_util_process_folder_videos",
    "API_util_restart_sync_microservice_watcher",
]


@pytest.fixture
def calls(monkeypatch: pytest.MonkeyPatch) -> List[str]:
    """Every stage replaced by a recorder; export goes through the real hook."""
    recorded: List[str] = []

    def recorder(name: str) -> Callable[..., object]:
        def stage(*args: object, **kwargs: object) -> object:
            recorded.append(name)
            return (0, 0) if name == "cluster_util_face_clusters_sync" else True

        return stage

    for name in PHOTO_STAGES + VIDEO_STAGES + OTHER:
        monkeypatch.setattr(folders, name, recorder(name))
    monkeypatch.setattr(exporter, "xmp_export_if_enabled", recorder("export"))
    return recorded


SEQUENCES = {
    "ai_tagging": lambda: folders.post_AI_tagging_enabled_sequence(),
    "sync_folder": lambda: folders.post_sync_folder_sequence("/p", "1", []),
}


@pytest.mark.parametrize("sequence", sorted(SEQUENCES))
def test_export_runs_once_after_photos_and_before_videos(calls, sequence):
    assert SEQUENCES[sequence]() is not False
    assert calls.count("export") == 1
    at = calls.index("export")
    assert all(calls.index(stage) < at for stage in PHOTO_STAGES)
    assert all(calls.index(stage) > at for stage in VIDEO_STAGES)


@pytest.mark.parametrize("sequence", sorted(SEQUENCES))
def test_a_failing_export_never_stops_the_pipeline(calls, sequence, monkeypatch):
    def broken() -> None:
        calls.append("export")
        raise OSError("disk full")

    monkeypatch.setattr(exporter, "xmp_export_if_enabled", broken)
    assert SEQUENCES[sequence]() is not False
    assert all(stage in calls for stage in VIDEO_STAGES)


def test_semantic_model_install_exports_after_the_new_embeddings():
    submitted: List[str] = []

    class Executor:
        def submit(self, fn: Callable[..., object], *args: object) -> None:
            submitted.append(fn.__name__)

    submit_embedding_backfill_if_semantic(["siglip2_base_vision"], Executor())  # type: ignore[arg-type]
    assert submitted[-1] == "xmp_export_if_enabled"
    assert submitted.index("semantic_util_score_images") < len(submitted) - 1


def test_non_semantic_model_install_queues_nothing():
    submitted: List[str] = []

    class Executor:
        def submit(self, fn: Callable[..., object], *args: object) -> None:
            submitted.append(fn.__name__)

    submit_embedding_backfill_if_semantic(["facenet"], Executor())  # type: ignore[arg-type]
    assert submitted == []


def test_startup_creates_and_shutdown_closes_the_debouncer():
    from fastapi.testclient import TestClient

    import main
    from app.utils.xmp.debounce import ExportDebouncer

    with TestClient(main.app):
        debouncer = main.app.state.metadata_export_debouncer
        assert isinstance(debouncer, ExportDebouncer)
    assert debouncer._closed
