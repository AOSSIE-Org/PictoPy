import threading
from concurrent.futures import Future, ProcessPoolExecutor
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from starlette.datastructures import State

from app.database.xmp_export_state import db_get_xmp_export_counts
from app.logging.setup_logging import get_logger
from app.routes.dependencies import get_state
from app.schemas.metadata_export import ErrorResponse
from app.utils.xmp.exporter import xmp_export_run

logger = get_logger(__name__)

router = APIRouter()


class ExportRunSummary(BaseModel):
    checked: int
    written: int
    unchanged: int
    skipped: int
    failed: int


class MetadataExportStatusData(BaseModel):
    # PNG images only: the one format PictoPy can write metadata into today.
    total: int
    pending: int
    # Pending images whose last write failed; the next pass retries them.
    failed: int
    # Left alone on purpose: unreadable XMP, or a newer PictoPy's data.
    skipped: int
    # State of the export started from Settings; automatic passes aren't tracked.
    running: bool = False
    run_failed: bool = False
    last_run: Optional[ExportRunSummary] = None


class MetadataExportStatusResponse(BaseModel):
    success: bool
    message: str
    data: MetadataExportStatusData


# Sync routes run on a threadpool, so two clicks could both see no run going.
_run_lock = threading.Lock()


def _status(app_state: State) -> MetadataExportStatusData:
    counts = db_get_xmp_export_counts()
    run: Optional[Future] = getattr(app_state, "metadata_export_run", None)
    running = run is not None and not run.done()
    finished = run is not None and run.done() and not run.cancelled()
    error = run.exception() if finished and run is not None else None
    return MetadataExportStatusData(
        **counts,
        running=running,
        run_failed=(run is not None and run.cancelled()) or error is not None,
        last_run=(
            ExportRunSummary(**run.result())
            if finished and run is not None and error is None
            else None
        ),
    )


@router.post(
    "/run",
    response_model=MetadataExportStatusResponse,
    responses={500: {"model": ErrorResponse}},
)
def run_metadata_export(
    app_state: State = Depends(get_state),
) -> MetadataExportStatusResponse:
    """Export the whole library now, whatever the automatic setting says.

    Also rechecks images already exported whose files changed since.
    """
    try:
        with _run_lock:
            if not _status(app_state).running:
                executor: ProcessPoolExecutor = app_state.executor
                app_state.metadata_export_run = executor.submit(xmp_export_run, True)

        status_data = _status(app_state)
        return MetadataExportStatusResponse(
            success=True,
            message=f"Exporting metadata for {status_data.total} PNG image(s)",
            data=status_data,
        )
    except Exception as e:
        logger.error(f"Error starting the metadata export: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                error="Internal server error",
                message=f"Unable to start the metadata export: {str(e)}",
            ).model_dump(),
        )


@router.get(
    "/status",
    response_model=MetadataExportStatusResponse,
    responses={500: {"model": ErrorResponse}},
)
def get_metadata_export_status(
    app_state: State = Depends(get_state),
) -> MetadataExportStatusResponse:
    """How much of the library holds up-to-date metadata, for a poller."""
    try:
        status_data = _status(app_state)
        return MetadataExportStatusResponse(
            success=True,
            message=f"{status_data.pending} of {status_data.total} PNG image(s) pending",
            data=status_data,
        )
    except Exception as e:
        logger.error(f"Error reading the metadata export status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                error="Internal server error",
                message=f"Unable to read the metadata export status: {str(e)}",
            ).model_dump(),
        )
