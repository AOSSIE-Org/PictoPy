import logging
from binascii import Error as Base64Error
import base64
from typing import Annotated
import uuid
import os
from fastapi import APIRouter, HTTPException, Query, status
from app.database.face_clusters import (
    db_get_cluster_by_id,
    db_update_cluster,
    db_get_all_clusters_with_face_counts,
    db_get_images_by_cluster_id,  # Add this import
)
from app.schemas.face_clusters import (
    RenameClusterRequest,
    RenameClusterResponse,
    RenameClusterData,
    ErrorResponse,
    GetClustersResponse,
    GetClustersData,
    ClusterMetadata,
    GetClusterImagesResponse,
    GetClusterImagesData,
    ImageInCluster,
)
from app.schemas.images import AddSingleBase64ImageRequest, AddSingleImageRequest, InputType
from app.utils.faceSearch import perform_face_search


logger = logging.getLogger(__name__)
router = APIRouter()


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
def face_tagging(payload: AddSingleImageRequest | AddSingleBase64ImageRequest, input_type: Annotated[InputType, Query(description="Choose input type: 'path' or 'base64'")] = InputType.path):
    image_path = None

    if input_type == InputType.path:
        if not os.path.isfile(payload.path):
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
        image_id = str(uuid.uuid4())[:8]
        temp_dir = "temp_uploads"
        os.makedirs(temp_dir, exist_ok=True)
        local_image_path = os.path.join(temp_dir, f"{image_id}.jpeg")

        with open(local_image_path, "wb") as f:
            f.write(image_bytes)

        image_path = local_image_path

    return perform_face_search(image_path)
