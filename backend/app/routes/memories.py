"""
Memories API routes.

Serves persisted, curated memories: the story viewer payload, the history
filmstrip, and the scheduler-facing status and generate endpoints.
"""

from concurrent.futures import ProcessPoolExecutor
from datetime import date
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from starlette.datastructures import State

from app.database.memories import (
    db_count_unviewed_memories,
    db_delete_memory,
    db_get_memory,
    db_get_memory_images,
    db_get_memory_videos,
    db_get_memory_run,
    db_get_surfaceable_memory,
    db_is_indexing_busy,
    db_list_memories,
    db_mark_memory,
    db_reap_stale_memory_runs,
    db_start_memory_run,
)
from app.logging.setup_logging import get_logger
from app.routes.dependencies import get_state
from app.schemas.memories import (
    DeleteMemoryData,
    DeleteMemoryResponse,
    ErrorResponse,
    GenerateMemoriesData,
    GenerateMemoriesRequest,
    GenerateMemoriesResponse,
    GetMemoriesData,
    GetMemoriesResponse,
    GetMemoryData,
    GetMemoryResponse,
    GetTodayMemoryData,
    GetTodayMemoryResponse,
    MemoryCard,
    MemoryImageItem,
    MemoryVideoItem,
    MemoryStatusData,
    MemoryStatusResponse,
    MemoryStory,
    UpdateMemoryRequest,
    UpdateMemoryResponse,
)
from app.utils.memory_curator import (
    memory_curator_get_preferences,
    memory_curator_params_signature,
    memory_curator_run,
)

router = APIRouter()
logger = get_logger(__name__)

# A run left 'running' past this window is treated as interrupted and reaped,
# so a crash mid-generation never permanently blocks the next run.
STALE_RUN_MINUTES = 30


def _internal_error(message: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=ErrorResponse(
            success=False, error="Internal server error", message=message
        ).model_dump(),
    )


def _not_found(memory_id: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=ErrorResponse(
            success=False,
            error="Not Found",
            message=f"No memory found with id {memory_id}",
        ).model_dump(),
    )


def _with_live_count(row: Dict[str, Any]) -> Dict[str, Any]:
    """Copy a memories row, preferring the live image count to the stored one."""
    data = dict(row)
    live_count = data.pop("live_image_count", None)
    if live_count is not None:
        data["image_count"] = live_count
    return data


def _to_card(row: Dict[str, Any]) -> MemoryCard:
    """Map a memories row to a card."""
    return MemoryCard.model_validate(_with_live_count(row))


def _to_story(row: Dict[str, Any]) -> MemoryStory:
    """Map a memories row plus its images to a full story payload."""
    data = _with_live_count(row)
    images = db_get_memory_images(data["memory_id"])
    videos = db_get_memory_videos(data["memory_id"])
    data["images"] = [MemoryImageItem.model_validate(image) for image in images]
    data["videos"] = [MemoryVideoItem.model_validate(video) for video in videos]
    return MemoryStory.model_validate(data)


@router.post(
    "/generate",
    response_model=GenerateMemoriesResponse,
    responses={code: {"model": ErrorResponse} for code in [400, 500]},
)
def generate_memories(
    request: GenerateMemoriesRequest, app_state: State = Depends(get_state)
):
    """
    Queue a curation run.

    Returns immediately; the run itself goes to the shared single-worker
    executor so it serializes behind indexing and semantic scoring rather than
    racing them.
    """
    try:
        try:
            reference = (
                date.fromisoformat(request.reference_date)
                if request.reference_date
                else date.today()
            )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse(
                    success=False,
                    error="Validation Error",
                    message="reference_date must be an ISO date (YYYY-MM-DD)",
                ).model_dump(),
            )
        run_date = reference.isoformat()

        db_reap_stale_memory_runs(STALE_RUN_MINUTES)
        run = db_get_memory_run(run_date)

        if run and run["status"] == "running":
            return GenerateMemoriesResponse(
                success=True,
                message="A curation run is already in progress",
                data=GenerateMemoriesData(
                    run_date=run_date, status="running", queued=False
                ),
            )

        if run and run["status"] == "complete" and not request.force:
            return GenerateMemoriesResponse(
                success=True,
                message="Memories for this date have already been generated",
                data=GenerateMemoriesData(
                    run_date=run_date, status="complete", queued=False
                ),
            )

        preferences = memory_curator_get_preferences()
        if not preferences.enabled and not request.force:
            # Claiming a run the curator is going to decline would leave the
            # row 'running' until the staleness window reaps it, blocking
            # every attempt in between.
            return GenerateMemoriesResponse(
                success=True,
                message="Memories are disabled",
                data=GenerateMemoriesData(
                    run_date=run_date, status="complete", queued=False
                ),
            )

        # Claim the run before handing off, so a second caller arriving while
        # the executor is still starting sees 'running' rather than queueing
        # a duplicate pass.
        db_start_memory_run(run_date, memory_curator_params_signature(preferences))

        executor: ProcessPoolExecutor = app_state.executor
        executor.submit(memory_curator_run, run_date, request.force, "api")

        return GenerateMemoriesResponse(
            success=True,
            message="Memory curation queued",
            data=GenerateMemoriesData(run_date=run_date, status="running", queued=True),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error queueing memory curation", exc_info=True)
        raise _internal_error(f"Unable to queue memory curation: {str(e)}")


@router.get(
    "/status",
    response_model=MemoryStatusResponse,
    responses={code: {"model": ErrorResponse} for code in [500]},
)
def get_memory_status():
    """
    Report scheduler state.

    Polled by the Tauri background task, which is why indexing_busy is computed
    here: the desktop shell never opens the database itself.
    """
    try:
        run_date = date.today().isoformat()
        db_reap_stale_memory_runs(STALE_RUN_MINUTES)
        run = db_get_memory_run(run_date)
        preferences = memory_curator_get_preferences()
        latest = db_get_surfaceable_memory(run_date)

        return MemoryStatusResponse(
            success=True,
            message="Successfully retrieved memory status",
            data=MemoryStatusData(
                run_date=run_date,
                run_status=run["status"] if run else None,
                run_started_at=run["started_at"] if run else None,
                indexing_busy=db_is_indexing_busy(),
                unviewed_count=db_count_unviewed_memories(run_date),
                latest_memory_id=latest["memory_id"] if latest else None,
                memories_enabled=preferences.enabled,
                notifications_enabled=preferences.notifications_enabled,
            ),
        )
    except Exception as e:
        logger.error("Error retrieving memory status", exc_info=True)
        raise _internal_error(f"Unable to retrieve memory status: {str(e)}")


@router.get(
    "/today",
    response_model=GetTodayMemoryResponse,
    responses={code: {"model": ErrorResponse} for code in [500]},
)
def get_today_memory():
    """
    Get the memory to surface now, or null if there is nothing to show.

    Having nothing to surface is a normal state for a small or new library, so
    this returns 200 with a null payload rather than a 404.
    """
    try:
        row = db_get_surfaceable_memory(date.today().isoformat())
        if not row:
            return GetTodayMemoryResponse(
                success=True,
                message="No memory available to surface",
                data=GetTodayMemoryData(memory=None),
            )
        return GetTodayMemoryResponse(
            success=True,
            message="Successfully retrieved today's memory",
            data=GetTodayMemoryData(memory=_to_story(row)),
        )
    except Exception as e:
        logger.error("Error retrieving today's memory", exc_info=True)
        raise _internal_error(f"Unable to retrieve today's memory: {str(e)}")


@router.get(
    "",
    response_model=GetMemoriesResponse,
    responses={code: {"model": ErrorResponse} for code in [500]},
)
def list_memories(
    limit: int = Query(30, ge=1, le=100, description="Maximum memories to return"),
    offset: int = Query(0, ge=0, description="Number of memories to skip"),
    event_type: Optional[str] = Query(
        None, description="Filter by anniversary, import_event or semantic_event"
    ),
    include_viewed: bool = Query(True, description="Include already-viewed memories"),
    include_dismissed: bool = Query(False, description="Include dismissed memories"),
):
    """List memory cards, newest first. Backs the history filmstrip and grid."""
    try:
        rows, total_count = db_list_memories(
            limit=limit,
            offset=offset,
            event_type=event_type,
            include_viewed=include_viewed,
            include_dismissed=include_dismissed,
        )
        return GetMemoriesResponse(
            success=True,
            message=f"Found {total_count} memories",
            data=GetMemoriesData(
                memories=[_to_card(row) for row in rows], total_count=total_count
            ),
        )
    except Exception as e:
        logger.error("Error listing memories", exc_info=True)
        raise _internal_error(f"Unable to list memories: {str(e)}")


@router.get(
    "/{memory_id}",
    response_model=GetMemoryResponse,
    responses={code: {"model": ErrorResponse} for code in [404, 500]},
)
def get_memory(memory_id: str):
    """Get a single memory with its full image set."""
    try:
        row = db_get_memory(memory_id)
        if not row:
            raise _not_found(memory_id)
        return GetMemoryResponse(
            success=True,
            message="Successfully retrieved memory",
            data=GetMemoryData(memory=_to_story(row)),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving memory {memory_id}", exc_info=True)
        raise _internal_error(f"Unable to retrieve memory: {str(e)}")


@router.patch(
    "/{memory_id}",
    response_model=UpdateMemoryResponse,
    responses={code: {"model": ErrorResponse} for code in [400, 404, 500]},
)
def update_memory(memory_id: str, request: UpdateMemoryRequest):
    """Update a memory's viewed, dismissed or notified state."""
    try:
        if (
            request.viewed is None
            and request.dismissed is None
            and request.notified is None
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse(
                    success=False,
                    error="Validation Error",
                    message="At least one of viewed, dismissed or notified is required",
                ).model_dump(),
            )

        if not db_get_memory(memory_id):
            raise _not_found(memory_id)

        db_mark_memory(
            memory_id,
            viewed=request.viewed,
            dismissed=request.dismissed,
            notified=request.notified,
        )

        row = db_get_memory(memory_id)
        if not row:
            raise _not_found(memory_id)

        return UpdateMemoryResponse(
            success=True,
            message="Successfully updated memory",
            data=GetMemoryData(memory=_to_story(row)),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating memory {memory_id}", exc_info=True)
        raise _internal_error(f"Unable to update memory: {str(e)}")


@router.delete(
    "/{memory_id}",
    response_model=DeleteMemoryResponse,
    responses={code: {"model": ErrorResponse} for code in [404, 500]},
)
def delete_memory(memory_id: str):
    """Delete a memory. Its curated image list cascades; the photos remain."""
    try:
        if not db_delete_memory(memory_id):
            raise _not_found(memory_id)
        return DeleteMemoryResponse(
            success=True,
            message="Successfully deleted memory",
            data=DeleteMemoryData(memory_id=memory_id),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting memory {memory_id}", exc_info=True)
        raise _internal_error(f"Unable to delete memory: {str(e)}")
