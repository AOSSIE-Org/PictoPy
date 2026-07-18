import os
import json
import uuid
import asyncio
from concurrent.futures import ProcessPoolExecutor
from typing import Dict, List
from dataclasses import dataclass, field
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
from starlette.datastructures import State
from app.models.model_registry import MODEL_REGISTRY, TIER_MODELS, get_model_path
from app.models.session_registry import (
    try_mark_model_for_deletion,
    release_model_deletion_mark,
    _registry_lock,
)
from app.utils.hardware_detect import get_hardware_info
from app.utils.images import image_util_process_unembedded_images
from app.utils.model_downloader import ensure_model
from app.database.metadata import db_get_metadata
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

REQUIRED_MODELS = ["facenet"]

SEMANTIC_FEATURES = ("semantic_vision", "semantic_text")


def get_state(request: Request) -> State:
    return request.app.state


def submit_embedding_backfill_if_semantic(
    model_keys: List[str], executor: ProcessPoolExecutor
) -> None:
    """Run the SigLIP2 embedding pass after a semantic model install.

    Covers images processed before the models were installed. The pass is
    self-gating and idempotent, so over-triggering is a cheap no-op.
    """
    if any(
        MODEL_REGISTRY[key].get("feature") in SEMANTIC_FEATURES for key in model_keys
    ):
        executor.submit(image_util_process_unembedded_images)


# Global dict to track download tasks
@dataclass
class DownloadTaskEntry:
    queue: asyncio.Queue
    task: asyncio.Task
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    active_listeners: int = 0
    listener_lock: asyncio.Lock = field(default_factory=asyncio.Lock)


download_tasks: Dict[str, DownloadTaskEntry] = {}

# Serialize downloads per model_key so concurrent tasks never write the same file path.
_model_download_locks: Dict[str, asyncio.Lock] = {}
_model_lock_registry_lock = asyncio.Lock()


async def _get_model_download_lock(model_key: str) -> asyncio.Lock:
    if model_key in _model_download_locks:
        return _model_download_locks[model_key]
    async with _model_lock_registry_lock:
        if model_key not in _model_download_locks:
            _model_download_locks[model_key] = asyncio.Lock()
        return _model_download_locks[model_key]


async def _cleanup_stale_tasks(max_age_minutes: int = 10):
    while True:
        await asyncio.sleep(300)  # run every 5 minutes
        now = datetime.now(timezone.utc)
        stale = [
            tid
            for tid, entry in download_tasks.items()
            if (now - entry.created_at).total_seconds() > max_age_minutes * 60
        ]
        for tid in stale:
            entry = download_tasks.pop(tid, None)
            if entry and not entry.task.done():
                entry.task.cancel()


class SetupRequest(BaseModel):
    tier: str


@router.get("/status")
def get_model_status():
    """
    Returns the installation status of all models in the registry.
    """
    status_dict = {}
    for key, spec in MODEL_REGISTRY.items():
        # Hide placeholder models that aren't actually ready/uploaded yet
        if spec["url"] == "PLACEHOLDER_URL" or spec["sha256"] == "PLACEHOLDER_SHA256":
            continue

        path = get_model_path(key)
        is_installed = os.path.exists(path)
        status_dict[key] = {
            "name": spec["filename"],
            "installed": is_installed,
            "feature": spec["feature"],
            "tier": spec["tier"],
            "size_mb": spec["size_mb"],
        }
    return {"success": True, "data": status_dict}


@router.get("/hardware")
def get_hardware_recommendation():
    """
    Returns hardware specs and the recommended model tier.
    """
    try:
        hw_info = get_hardware_info()
        return {"success": True, "data": hw_info}
    except Exception as e:
        logger.error(f"Failed to get hardware info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to detect hardware: {str(e)}",
        )


@router.delete("/{model_key}")
async def delete_model(model_key: str):
    """
    Deletes a specific model from disk.
    """
    if model_key not in MODEL_REGISTRY:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model key '{model_key}' not found in registry.",
        )

    spec = MODEL_REGISTRY[model_key]

    # Guard 1: Prevent deletion of required models
    if spec.get("tier") == "required":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete a required model. No fallback exists for this slot.",
        )

    with _registry_lock:
        # Guard 2: Prevent deletion of the currently active tier
        metadata = db_get_metadata()
        active_tier = "small"  # Default model size if no preferences found
        if metadata and "user_preferences" in metadata:
            user_prefs = metadata["user_preferences"]
            active_tier = user_prefs.get("YOLO_model_size", "small")

        if spec.get("tier") == active_tier:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot delete model '{model_key}' because its tier '{spec.get('tier')}' is currently active. Switch to a different tier before deleting.",
            )

        # The SigLIP2 text model is kept in a persistent cross-request cache
        # (see siglip_util_get_text_model) whose session would otherwise stay
        # registered as "active" forever, permanently blocking the guard below.
        if spec.get("feature") == "semantic_text":
            from app.utils.SigLIP import siglip_util_invalidate_text_model

            siglip_util_invalidate_text_model(model_key)

        # Check no sessions are active and reserve the model for deletion.
        active_session_count = try_mark_model_for_deletion(model_key)
        if active_session_count is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Model {model_key} is currently in use by {active_session_count} active session(s). "
                    "Close active model sessions before deleting."
                ),
            )

    path = get_model_path(model_key)

    try:
        if os.path.exists(path):
            try:
                await asyncio.to_thread(os.remove, path)
                return {
                    "success": True,
                    "message": f"Model {model_key} deleted successfully.",
                }
            except Exception as e:
                logger.error(f"Failed to delete model {model_key}: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to delete model: {str(e)}",
                )
        else:
            return {
                "success": True,
                "message": f"Model {model_key} already not present.",
            }
    finally:
        release_model_deletion_mark(model_key)


@router.post("/setup")
async def setup_models(request: SetupRequest, app_state: State = Depends(get_state)):
    """
    Initializes setup by starting downloads for a specific tier + required models.
    Returns a single task_id to track overall progress.
    """
    if request.tier not in TIER_MODELS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid tier '{request.tier}'. Valid tiers are: {list(TIER_MODELS.keys())}",
        )

    models_to_download = (
        TIER_MODELS[request.tier]
        if request.tier == "required"
        else TIER_MODELS[request.tier] + REQUIRED_MODELS
    )

    task_id = str(uuid.uuid4())
    queue = asyncio.Queue()

    async def background_setup():
        try:
            total_models = len(models_to_download)
            for idx, model_key in enumerate(models_to_download):

                def progress_callback(
                    percent: float,
                    downloaded: int,
                    total: int,
                    *,
                    _model_key: str = model_key,
                    _idx: int = idx,
                    _total_models: int = total_models,
                ):
                    # Send progress update
                    queue.put_nowait(
                        {
                            "status": "downloading",
                            "model_key": _model_key,
                            "model_index": _idx + 1,
                            "total_models": _total_models,
                            "percent": percent,
                            "downloaded": downloaded,
                            "total": total,
                        }
                    )

                model_lock = await _get_model_download_lock(model_key)
                async with model_lock:
                    await ensure_model(model_key, progress_callback=progress_callback)

            submit_embedding_backfill_if_semantic(
                models_to_download, app_state.executor
            )
            queue.put_nowait({"status": "complete"})
        except Exception as e:
            logger.error(f"Error during setup download: {e}")
            queue.put_nowait({"status": "error", "message": str(e)})

    # Start the setup in the background
    task = asyncio.create_task(background_setup())
    download_tasks[task_id] = DownloadTaskEntry(queue=queue, task=task)

    return {
        "success": True,
        "task_id": task_id,
        "message": f"Setup started for tier '{request.tier}'",
    }


@router.post("/download/{model_key}")
async def start_download_model(model_key: str, app_state: State = Depends(get_state)):
    """
    Starts download for a specific model by key. Returns a task_id.
    """
    if model_key not in MODEL_REGISTRY:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model key '{model_key}' not found in registry.",
        )

    task_id = str(uuid.uuid4())
    queue = asyncio.Queue()

    async def background_download():
        try:

            def progress_callback(percent: float, downloaded: int, total: int):
                queue.put_nowait(
                    {
                        "status": "downloading",
                        "model_key": model_key,
                        "percent": percent,
                        "downloaded": downloaded,
                        "total": total,
                    }
                )

            model_lock = await _get_model_download_lock(model_key)
            async with model_lock:
                await ensure_model(model_key, progress_callback=progress_callback)
            submit_embedding_backfill_if_semantic([model_key], app_state.executor)
            queue.put_nowait({"status": "complete", "model_key": model_key})
        except Exception as e:
            logger.error(f"Error downloading model {model_key}: {e}")
            queue.put_nowait({"status": "error", "message": str(e)})

    # Start the download in the background
    task = asyncio.create_task(background_download())
    download_tasks[task_id] = DownloadTaskEntry(queue=queue, task=task)

    return {
        "success": True,
        "task_id": task_id,
        "message": f"Download started for {model_key}",
    }


@router.get("/download/{task_id}/progress")
async def download_progress(task_id: str):
    """
    Streams SSE progress for a given download task_id.
    """
    entry = download_tasks.get(task_id)
    if entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task ID not found or already completed.",
        )

    async with entry.listener_lock:
        if entry.active_listeners > 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Another client is already subscribed to this download stream.",
            )
        entry.active_listeners += 1

    async def event_generator():
        completed_normally = False
        try:
            while True:
                try:
                    msg = await asyncio.wait_for(entry.queue.get(), timeout=15.0)
                except asyncio.TimeoutError:
                    yield "event: heartbeat\ndata: {}\n\n"
                    continue

                if msg["status"] == "complete":
                    yield f"data: {json.dumps(msg)}\n\n"
                    completed_normally = True
                    break
                if msg["status"] == "error":
                    yield f"data: {json.dumps(msg)}\n\n"
                    completed_normally = True
                    break
                yield f"data: {json.dumps(msg)}\n\n"
        except asyncio.CancelledError:
            # Disconnect: release listener slot only; download continues.
            raise
        finally:
            async with entry.listener_lock:
                entry.active_listeners = max(0, entry.active_listeners - 1)
            if completed_normally:
                download_tasks.pop(task_id, None)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
