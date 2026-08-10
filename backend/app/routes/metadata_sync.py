from fastapi import APIRouter, HTTPException, Query, status

from app.database.metadata_sync import db_count_images_pending_metadata_sync
from app.logging.setup_logging import get_logger
from app.schemas.metadata_sync import (
    ErrorResponse,
    GetMetadataSyncStatusResponse,
    MetadataSyncResult,
    MetadataSyncStatus,
    RunMetadataSyncResponse,
)
from app.utils.metadata_sync import (
    metadata_util_sync_pending,
    metadata_util_write_to_files_enabled,
)

logger = get_logger(__name__)

router = APIRouter()


@router.get(
    "/status",
    response_model=GetMetadataSyncStatusResponse,
    responses={500: {"model": ErrorResponse}},
)
def get_metadata_sync_status():
    """How many photos are waiting to have their metadata written to disk."""
    try:
        return GetMetadataSyncStatusResponse(
            success=True,
            message="Successfully retrieved metadata sync status",
            data=MetadataSyncStatus(
                enabled=metadata_util_write_to_files_enabled(),
                pending=db_count_images_pending_metadata_sync(),
            ),
        )
    except Exception as e:
        logger.error(f"Error retrieving metadata sync status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                error="Internal Server Error",
                message=f"Unable to retrieve metadata sync status: {e}",
            ).model_dump(),
        )


@router.post(
    "/run",
    response_model=RunMetadataSyncResponse,
    responses={500: {"model": ErrorResponse}},
)
def run_metadata_sync(limit: int = Query(default=200, ge=1, le=5000)):
    """
    Write pending metadata into the photo files.

    Does nothing unless the user has turned file writing on; the response still
    reports what was considered so the caller can tell the difference.
    """
    try:
        summary = metadata_util_sync_pending(limit)
        return RunMetadataSyncResponse(
            success=True,
            message=(
                "Metadata sync complete"
                if summary.get("disabled") is None
                else "Writing metadata to files is turned off"
            ),
            data=MetadataSyncResult(
                considered=summary["considered"],
                written=summary["written"],
                skipped=summary["skipped"],
            ),
        )
    except Exception as e:
        logger.error(f"Error running metadata sync: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                error="Internal Server Error",
                message=f"Unable to run metadata sync: {e}",
            ).model_dump(),
        )
