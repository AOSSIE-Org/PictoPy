import logging
from binascii import Error as Base64Error
import base64
from concurrent.futures import CancelledError, Future, ProcessPoolExecutor
from typing import Annotated, Optional
import os
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.database.face_clusters import (
    db_get_cluster_by_id,
    db_update_cluster,
    db_get_all_clusters_with_face_counts,
    db_get_images_by_cluster_id,
    db_get_images_by_face_clusters,
)
from starlette.datastructures import State

from app.routes.dependencies import get_state
from app.utils.face_clusters import cluster_util_face_clusters_sync
from app.schemas.face_clusters import (
    RenameClusterRequest,
    RenameClusterResponse,
    RenameClusterData,
    ErrorResponse,
    GetClustersResponse,
    GetClustersData,
    GlobalReclusterResponse,
    GlobalReclusterData,
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
from app.database.folders import db_get_all_folders

logger = logging.getLogger(__name__)
router = APIRouter()


def get_safe_root(target_path: str) -> Optional[str]:
    """Validate that target_path is within one of the registered folders or temp_uploads
    and return the matching resolved folder root.
    """
    real_target = os.path.realpath(target_path)
    try:
        allowed_folders = db_get_all_folders()
    except Exception:
        allowed_folders = []

    temp_dir = os.path.realpath("temp_uploads")
    allowed_folders.append(temp_dir)

    for folder in allowed_folders:
        real_folder = os.path.realpath(folder)
        try:
            if os.path.commonpath([real_folder, real_target]) == real_folder:
                return real_folder
        except ValueError:
            continue
    return None


def is_safe_path(target_path: str) -> bool:
    """Validate that target_path is within one of the registered folders or temp_uploads."""
    return get_safe_root(target_path) is not None


def _log_rescore_outcome(cluster_id: str, done: "Future[int]") -> None:
    """
    Report a rescore that died in the worker.

    A submitted job's exception surfaces only through its Future, so without
    this a failed rescore is silent. The rename itself already stands.
    """
    try:
        done.result()
    except CancelledError:
        logger.info(f"Memory rescore for cluster {cluster_id} was cancelled")
    except Exception:
        logger.error(f"Memory rescore for cluster {cluster_id} failed", exc_info=True)


def _rescore_memories_for_cluster(app_state: State, cluster_id: str) -> None:
    """
    Queue a rescore of memories containing this cluster.

    Offloaded to the shared executor and swallowed on failure: renaming a
    person must succeed whether or not memories can be refreshed.
    """
    try:
        from app.utils.memory_curator import memory_curator_rescore_for_cluster

        executor: ProcessPoolExecutor = app_state.executor
        future = executor.submit(memory_curator_rescore_for_cluster, cluster_id)
        future.add_done_callback(lambda done: _log_rescore_outcome(cluster_id, done))
    except Exception as e:
        logger.error(f"Failed to queue memory rescore for cluster {cluster_id}: {e}")


@router.put(
    "/{cluster_id}",
    response_model=RenameClusterResponse,
    responses={code: {"model": ErrorResponse} for code in [400, 404, 500]},
)
def rename_cluster(
    cluster_id: str,
    request: RenameClusterRequest,
    app_state: State = Depends(get_state),
):
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

        # Naming a person raises the known_people signal for every photo they
        # appear in, so memories already holding those photos are now ranked
        # on stale inputs.
        _rescore_memories_for_cluster(app_state, cluster_id)

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
        allowed_root = get_safe_root(local_file_path)
        if not allowed_root:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=ErrorResponse(
                    success=False,
                    error="Access Denied",
                    message="Access to the specified file path is restricted.",
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

        from pathlib import Path

        canonical_root = os.path.realpath(allowed_root)
        canonical_target = os.path.realpath(local_file_path)
        rel_path = os.path.relpath(canonical_target, canonical_root)
        components = Path(rel_path).parts

        dir_fd_supported = os.open in os.supports_dir_fd

        if dir_fd_supported:
            fd = None
            try:
                # Open the allowed root directory
                fd = os.open(canonical_root, os.O_RDONLY | os.O_DIRECTORY)

                # Walk through the subdirectories resolving relative components
                for comp in components[:-1]:
                    if comp == "." or not comp:
                        continue
                    next_fd = os.open(
                        comp, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd
                    )
                    os.close(fd)
                    fd = next_fd

                # Open the final file component with O_NOFOLLOW
                final_comp = components[-1]
                file_flags = os.O_RDONLY | os.O_NOFOLLOW
                file_fd = os.open(final_comp, file_flags, dir_fd=fd)
                os.close(fd)
                fd = None  # fd is closed, only file_fd remains open

                # Verify that it is a regular file
                stat_result = os.fstat(file_fd)
                import stat

                if not stat.S_ISREG(stat_result.st_mode):
                    os.close(file_fd)
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=ErrorResponse(
                            success=False,
                            error="Invalid file",
                            message="The target path is not a regular file.",
                        ).model_dump(),
                    )

                with open(file_fd, "rb") as f:
                    image_bytes = f.read()
            except Exception as e:
                if fd is not None:
                    try:
                        os.close(fd)
                    except Exception:
                        pass
                logger.error(
                    f"Failed to securely walk and open path {local_file_path}: {e}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=ErrorResponse(
                        success=False,
                        error="Access Denied",
                        message="Cannot read the specified path.",
                    ).model_dump(),
                )
        else:
            # Fallback for platforms where dir_fd is not supported (Windows)
            try:
                flags = os.O_RDONLY
                if hasattr(os, "O_NOFOLLOW"):
                    flags |= os.O_NOFOLLOW
                fd_handle = os.open(local_file_path, flags)

                # Verify regular file using fstat on the opened fd
                stat_result = os.fstat(fd_handle)
                import stat

                if not stat.S_ISREG(stat_result.st_mode):
                    os.close(fd_handle)
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=ErrorResponse(
                            success=False,
                            error="Invalid file",
                            message="The target path is not a regular file.",
                        ).model_dump(),
                    )

                with open(fd_handle, "rb") as f:
                    image_bytes = f.read()
            except Exception as e:
                logger.error(f"Failed to securely open path {local_file_path}: {e}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=ErrorResponse(
                        success=False,
                        error="Access Denied",
                        message="Cannot read the specified path.",
                    ).model_dump(),
                )

        return perform_face_search(image_bytes=image_bytes)

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

        return perform_face_search(image_bytes=image_bytes)


@router.post(
    "/global-recluster",
    response_model=GlobalReclusterResponse,
    responses={code: {"model": ErrorResponse} for code in [500]},
)
def trigger_global_reclustering():
    """
    Manually trigger global face reclustering.
    This forces full reclustering regardless of the 24-hour rule.
    """
    try:
        logger.info("Starting manual global face reclustering...")

        result, total_faces_skipped = cluster_util_face_clusters_sync(
            force_full_reclustering=True
        )

        if result == 0:
            return GlobalReclusterResponse(
                success=True,
                message="No faces found to cluster",
                data=GlobalReclusterData(
                    clusters_created=0, faces_skipped=total_faces_skipped
                ),
            )

        logger.info("Global reclustering completed successfully")

        return GlobalReclusterResponse(
            success=True,
            message="Global reclustering completed successfully.",
            data=GlobalReclusterData(
                clusters_created=result, faces_skipped=total_faces_skipped
            ),
        )

    except Exception as e:
        logger.error(f"Global reclustering failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                error="Internal server error",
                message=f"Global reclustering failed: {str(e)}",
            ).model_dump(),
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
