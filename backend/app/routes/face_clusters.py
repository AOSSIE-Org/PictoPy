import asyncio
import logging
from binascii import Error as Base64Error
import base64
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Annotated, Dict, Optional
import uuid
import os
from fastapi import APIRouter, HTTPException, Query, status
from app.database.face_clusters import (
    db_get_cluster_by_id,
    db_update_cluster,
    db_get_all_clusters_with_face_counts,
    db_get_images_by_cluster_id,
    db_get_images_by_face_clusters,
)
from app.utils.face_clusters import cluster_util_face_clusters_sync
from app.schemas.face_clusters import (
    RenameClusterRequest,
    RenameClusterResponse,
    RenameClusterData,
    ErrorResponse,
    GetClustersResponse,
    GetClustersData,
    GlobalReclusterStartData,
    GlobalReclusterStartResponse,
    GlobalReclusterStatusData,
    GlobalReclusterStatusResponse,
    ClusterMetadata,
    GetClusterImagesResponse,
    GetClusterImagesData,
    ImageInCluster,
    MultiPersonSearchRequest,
    MultiPersonSearchResponse,
    MultiPersonSearchData,
    MultiPersonSearchImage,
)
from app.schemas.images import FaceSearchRequest, InputType
from app.utils.faceSearch import perform_face_search

logger = logging.getLogger(__name__)
router = APIRouter()


# Global reclustering runs synchronously over every face embedding in the
# library and can take well past any reasonable HTTP timeout on large
# libraries, so it runs as a background task that the client polls instead
# of blocking the request.
@dataclass
class ReclusterTask:
    status: str = "running"  # running | complete | error
    clusters_created: Optional[int] = None
    faces_skipped: Optional[int] = None
    message: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: Optional[datetime] = None
    task: Optional[asyncio.Task] = None


recluster_tasks: Dict[str, ReclusterTask] = {}

# Only one global reclustering job may run at a time: a full pass deletes and
# rebuilds every cluster, so two concurrent runs would race on the same tables.
# Holds the task_id of the in-flight job, or None when idle. Safe without a
# lock because it is only read/written from the (single-threaded) event loop
# with no await between check-and-set.
_active_recluster_task_id: Optional[str] = None

# How long a finished task's result is retained for polling, measured from when
# it finished (not when it started) so a long-running job's result isn't reaped
# almost immediately after completion. Running tasks are never reaped (they are
# bounded to one by the concurrency guard above).
RECLUSTER_TASK_TTL_MINUTES = 15


async def _run_global_recluster(task_id: str):
    global _active_recluster_task_id
    entry = recluster_tasks[task_id]
    try:
        result, total_faces_skipped = await asyncio.to_thread(
            cluster_util_face_clusters_sync, force_full_reclustering=True
        )

        entry.status = "complete"
        entry.clusters_created = result or 0
        entry.faces_skipped = total_faces_skipped
        entry.message = (
            "No faces found to cluster"
            if not result
            else "Global reclustering completed successfully."
        )
        logger.info("Global reclustering completed successfully (task_id=%s)", task_id)
    except Exception as e:
        logger.error(f"Global reclustering failed: {str(e)}")
        entry.status = "error"
        entry.message = f"Global reclustering failed: {str(e)}"
    finally:
        # Stamp completion time so cleanup ages the result from when it finished,
        # and release the concurrency guard so a new job can be started, while
        # the finished result stays in recluster_tasks for the client to poll.
        entry.finished_at = datetime.now(timezone.utc)
        if _active_recluster_task_id == task_id:
            _active_recluster_task_id = None


async def _cleanup_stale_recluster_tasks():
    """Periodically drop finished reclustering results once they age out.

    Running tasks are left untouched (a legitimate recluster can run for a
    long time, and the concurrency guard already bounds them to one).
    """
    while True:
        await asyncio.sleep(300)  # run every 5 minutes
        now = datetime.now(timezone.utc)
        stale = [
            tid
            for tid, entry in recluster_tasks.items()
            if entry.status != "running"
            and entry.finished_at is not None
            and (now - entry.finished_at).total_seconds()
            > RECLUSTER_TASK_TTL_MINUTES * 60
        ]
        for tid in stale:
            recluster_tasks.pop(tid, None)


@router.put(
    "/{cluster_id}",
    response_model=RenameClusterResponse,
    responses={code: {"model": ErrorResponse} for code in [400, 404, 500]},
)
def rename_cluster(cluster_id: str, request: RenameClusterRequest):
    """Rename a face cluster by its ID."""
    try:
        # Step 1: Data Validation
        if not cluster_id.strip():
            raise ValueError("Cluster ID cannot be empty")

        if not request.cluster_name.strip():
            raise ValueError("Cluster name cannot be empty")

        # Step 2: Check if cluster exists
        existing_cluster = db_get_cluster_by_id(cluster_id)
        if not existing_cluster:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse(
                    success=False,
                    error="Cluster Not Found",
                    message=f"Cluster with ID '{cluster_id}' does not exist.",
                ).model_dump(),
            )

        # Step 3: Update cluster name
        updated = db_update_cluster(
            cluster_id=cluster_id,
            cluster_name=request.cluster_name.strip(),
        )

        if not updated:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ErrorResponse(
                    success=False,
                    error="Update Failed",
                    message=f"Failed to update cluster '{cluster_id}'.",
                ).model_dump(),
            )

        return RenameClusterResponse(
            success=True,
            message=f"Successfully renamed cluster to '{request.cluster_name}'",
            data=RenameClusterData(
                cluster_id=cluster_id,
                cluster_name=request.cluster_name.strip(),
            ),
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                success=False,
                error="Validation Error",
                message=str(e),
            ).model_dump(),
        )
    except HTTPException as e:
        # Re-raise HTTPExceptions to preserve the status code and detail
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                error="Internal server error",
                message=f"Unable to rename cluster: {str(e)}",
            ).model_dump(),
        )


@router.get(
    "/",
    response_model=GetClustersResponse,
    responses={code: {"model": ErrorResponse} for code in [500]},
)
def get_all_clusters():
    """Get metadata for all face clusters including face counts."""
    try:
        clusters_data = db_get_all_clusters_with_face_counts()

        clusters = [
            ClusterMetadata(
                cluster_id=cluster["cluster_id"],
                cluster_name=cluster["cluster_name"],
                face_count=cluster["face_count"],
                face_image_base64=cluster["face_image_base64"],
            )
            for cluster in clusters_data
        ]

        return GetClustersResponse(
            success=True,
            message=f"Successfully retrieved {len(clusters)} cluster(s)",
            data=GetClustersData(clusters=clusters),
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                error="Internal server error",
                message=f"Unable to retrieve clusters: {str(e)}",
            ).model_dump(),
        )


@router.get(
    "/{cluster_id}/images",
    response_model=GetClusterImagesResponse,
    responses={code: {"model": ErrorResponse} for code in [404, 500]},
)
def get_cluster_images(cluster_id: str):
    """Get all images that contain faces belonging to a specific cluster."""
    try:
        # Step 1: Validate cluster exists
        cluster = db_get_cluster_by_id(cluster_id)
        if not cluster:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse(
                    success=False,
                    error="Cluster Not Found",
                    message=f"Cluster with ID '{cluster_id}' does not exist.",
                ).model_dump(),
            )

        # Step 2: Get images for this cluster
        images_data = db_get_images_by_cluster_id(cluster_id)

        # Step 3: Convert to response models
        images = [
            ImageInCluster(
                id=img["image_id"],
                path=img["image_path"],
                thumbnailPath=img["thumbnail_path"],
                metadata=img["metadata"],
                face_id=img["face_id"],
                confidence=img["confidence"],
                bbox=img["bbox"],
            )
            for img in images_data
        ]

        return GetClusterImagesResponse(
            success=True,
            message=f"Successfully retrieved {len(images)} image(s) for cluster '{cluster_id}'",
            data=GetClusterImagesData(
                cluster_id=cluster_id,
                cluster_name=cluster["cluster_name"],
                images=images,
                total_images=len(images),
            ),
        )

    except HTTPException as e:
        # Re-raise HTTPExceptions to preserve the status code and detail
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                error="Internal server error",
                message=f"Unable to retrieve images for cluster: {str(e)}",
            ).model_dump(),
        )


@router.post(
    "/face-search",
    responses={code: {"model": ErrorResponse} for code in [400, 500]},
)
def face_tagging(
    payload: FaceSearchRequest,
    input_type: Annotated[
        InputType, Query(description="Choose input type: 'path' or 'base64'")
    ] = InputType.path,
):
    image_path = None

    if input_type == InputType.path:
        local_file_path = payload.path

        if not local_file_path:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse(
                    success=False,
                    error="No Image path provided ",
                    message="image path is required.",
                ).model_dump(),
            )
        if not os.path.isfile(local_file_path):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse(
                    success=False,
                    error="Invalid file path",
                    message="The provided path is not a valid file",
                ).model_dump(),
            )
        image_path = payload.path

    elif input_type == InputType.base64:
        base64_data = payload.base64_data
        if not base64_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse(
                    success=False,
                    error="No base64 data",
                    message="Base64 image data is required.",
                ).model_dump(),
            )

        MAX_B64_LEN = 14_000_000  # 10MB
        if len(base64_data) > MAX_B64_LEN:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse(
                    success=False,
                    error="Payload too large",
                    message="Base64 image exceeds maximum allowed size.",
                ).model_dump(),
            )
        try:
            image_bytes = base64.b64decode(base64_data.split(",")[-1])
        except (Base64Error, ValueError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse(
                    success=False,
                    error="Invalid base64 data",
                    message="The provided base64 image data is malformed or invalid.",
                ).model_dump(),
            )

        format_match = (
            base64_data.split(";")[0].split("/")[-1] if ";" in base64_data else "jpeg"
        )
        extension = (
            format_match
            if format_match in ["jpeg", "jpg", "png", "gif", "webp"]
            else "jpeg"
        )
        image_id = str(uuid.uuid4())[:8]
        temp_dir = "temp_uploads"
        os.makedirs(temp_dir, exist_ok=True)
        local_image_path = os.path.join(temp_dir, f"{image_id}.{extension}")

        with open(local_image_path, "wb") as f:
            f.write(image_bytes)

        image_path = local_image_path

    try:
        return perform_face_search(image_path)
    finally:
        if input_type == InputType.base64 and image_path and os.path.exists(image_path):
            os.remove(image_path)


@router.post(
    "/global-recluster",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=GlobalReclusterStartResponse,
    responses={code: {"model": ErrorResponse} for code in [500]},
)
async def trigger_global_reclustering():
    """
    Start a global face reclustering job in the background.
    This forces full reclustering regardless of the 24-hour rule.

    Returns immediately with a task_id; poll
    GET /face-clusters/global-recluster/{task_id} for the result, since
    reclustering runs over every face embedding and can take a long time
    on large libraries.

    If a reclustering job is already running, its task_id is returned instead
    of starting a second (concurrent runs would race on the cluster tables).
    """
    global _active_recluster_task_id

    if _active_recluster_task_id is not None:
        logger.info(
            "Global reclustering already in progress (task_id=%s); reusing it",
            _active_recluster_task_id,
        )
        return GlobalReclusterStartResponse(
            success=True,
            message="Global reclustering already in progress.",
            data=GlobalReclusterStartData(task_id=_active_recluster_task_id),
        )

    task_id = str(uuid.uuid4())
    entry = ReclusterTask()
    recluster_tasks[task_id] = entry
    _active_recluster_task_id = task_id
    entry.task = asyncio.create_task(_run_global_recluster(task_id))

    logger.info("Started manual global face reclustering (task_id=%s)", task_id)

    return GlobalReclusterStartResponse(
        success=True,
        message="Global reclustering started.",
        data=GlobalReclusterStartData(task_id=task_id),
    )


@router.get(
    "/global-recluster/{task_id}",
    response_model=GlobalReclusterStatusResponse,
    responses={code: {"model": ErrorResponse} for code in [404]},
)
async def get_global_recluster_status(task_id: str):
    """Poll the status of a previously started global reclustering job."""
    entry = recluster_tasks.get(task_id)
    if entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                success=False,
                error="Task Not Found",
                message=f"Recluster task '{task_id}' not found or expired.",
            ).model_dump(),
        )

    if entry.status == "running":
        return GlobalReclusterStatusResponse(
            success=True,
            data=GlobalReclusterStatusData(status="running"),
        )

    # Terminal state: leave the entry in place so repeated polls (multiple
    # tabs, retries) return the same result; _cleanup_stale_recluster_tasks
    # reaps it once it ages out.
    if entry.status == "error":
        return GlobalReclusterStatusResponse(
            success=False,
            message=entry.message,
            data=GlobalReclusterStatusData(status="error"),
        )

    return GlobalReclusterStatusResponse(
        success=True,
        message=entry.message,
        data=GlobalReclusterStatusData(
            status="complete",
            clusters_created=entry.clusters_created,
            faces_skipped=entry.faces_skipped,
        ),
    )


@router.post(
    "/multi-search",
    response_model=MultiPersonSearchResponse,
    responses={code: {"model": ErrorResponse} for code in [400, 404, 500]},
)
def search_images_by_multiple_faces(body: MultiPersonSearchRequest):
    """Search for images containing multiple face identities, ranked by match count."""
    try:
        if not body.cluster_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse(
                    success=False,
                    error="Validation Error",
                    message="cluster_ids cannot be empty.",
                ).model_dump(),
            )
        if body.match_mode not in ("match_any", "match_all"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse(
                    success=False,
                    error="Validation Error",
                    message="match_mode must be 'match_any' or 'match_all'.",
                ).model_dump(),
            )

        rows = db_get_images_by_face_clusters(body.cluster_ids, body.match_mode)

        images = [
            MultiPersonSearchImage(
                id=row["image_id"],
                path=row["image_path"],
                thumbnailPath=row["thumbnail_path"],
                metadata=row["metadata"],
                match_count=row["match_count"],
            )
            for row in rows
        ]

        return MultiPersonSearchResponse(
            success=True,
            message=f"Found {len(images)} image(s) matching the selected people.",
            data=MultiPersonSearchData(
                images=images,
                total=len(images),
                match_mode=body.match_mode,
            ),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                error="Internal server error",
                message=f"Multi-person search failed: {str(e)}",
            ).model_dump(),
        )
