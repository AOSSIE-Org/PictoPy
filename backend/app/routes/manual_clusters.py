"""
RESTful API endpoints for manual cluster management.

Routes
------
POST   /clusters/                        – Create cluster
GET    /clusters/                        – List all clusters
GET    /clusters/{cluster_id}            – Get cluster + images
PATCH  /clusters/{cluster_id}            – Rename cluster
DELETE /clusters/{cluster_id}            – Delete cluster
POST   /clusters/{cluster_id}/images     – Bulk-assign images
DELETE /clusters/{cluster_id}/images/{image_id} – Remove image
"""

import logging

from fastapi import APIRouter, HTTPException, Path, status

from app.schemas.manual_clusters import (
    AssignImagesRequest,
    AssignImagesResponse,
    ClusterDetail,
    ClusterSummary,
    CreateClusterRequest,
    CreateClusterResponse,
    DeleteClusterResponse,
    ErrorResponse,
    GetAllClustersResponse,
    GetClusterDetailResponse,
    RemoveImageResponse,
    RenameClusterRequest,
    RenameClusterResponse,
)
from app.utils.manual_cluster_service import (
    ClusterNotFoundError,
    DuplicateClusterNameError,
    ImageNotFoundError,
    assign_images,
    create_cluster,
    delete_cluster,
    get_cluster,
    list_clusters,
    remove_image,
    rename_cluster,
)

logger = logging.getLogger(__name__)
router = APIRouter()

_ERR_RESPONSES = {code: {"model": ErrorResponse} for code in [400, 404, 409, 500]}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _not_found(cluster_id: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=ErrorResponse(
            success=False,
            error="Cluster Not Found",
            message=f"Cluster '{cluster_id}' does not exist.",
        ).model_dump(),
    )


def _bad_request(msg: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=ErrorResponse(
            success=False,
            error="Bad Request",
            message=msg,
        ).model_dump(),
    )


def _conflict(msg: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=ErrorResponse(
            success=False,
            error="Conflict",
            message=msg,
        ).model_dump(),
    )


# ---------------------------------------------------------------------------
# POST /clusters/  – Create
# ---------------------------------------------------------------------------


@router.post(
    "/",
    response_model=CreateClusterResponse,
    status_code=status.HTTP_201_CREATED,
    responses=_ERR_RESPONSES,
    summary="Create a new manual cluster",
)
def create_cluster_endpoint(body: CreateClusterRequest):
    """Create a user-defined cluster that is independent of AI face clusters."""
    try:
        record = create_cluster(body.name)
        return CreateClusterResponse(
            success=True,
            message=f"Cluster '{record['name']}' created successfully.",
            data=ClusterSummary(**record),
        )
    except DuplicateClusterNameError as exc:
        raise _conflict(str(exc))
    except ValueError as exc:
        raise _bad_request(str(exc))
    except Exception as exc:
        logger.exception("Unexpected error creating cluster")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False, error="Internal Error", message=str(exc)
            ).model_dump(),
        )


# ---------------------------------------------------------------------------
# GET /clusters/  – List
# ---------------------------------------------------------------------------


@router.get(
    "/",
    response_model=GetAllClustersResponse,
    responses=_ERR_RESPONSES,
    summary="List all manual clusters",
)
def list_clusters_endpoint():
    """Return all manually created clusters with image counts."""
    try:
        clusters = list_clusters()
        return GetAllClustersResponse(
            success=True,
            data=[ClusterSummary(**c) for c in clusters],
        )
    except Exception as exc:
        logger.exception("Unexpected error listing clusters")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False, error="Internal Error", message=str(exc)
            ).model_dump(),
        )


# ---------------------------------------------------------------------------
# GET /clusters/{cluster_id}  – Detail
# ---------------------------------------------------------------------------


@router.get(
    "/{cluster_id}",
    response_model=GetClusterDetailResponse,
    responses=_ERR_RESPONSES,
    summary="Get cluster details including images",
)
def get_cluster_endpoint(cluster_id: str = Path(...)):
    """Retrieve a cluster and all images assigned to it."""
    try:
        detail = get_cluster(cluster_id)
        return GetClusterDetailResponse(
            success=True,
            data=ClusterDetail(
                cluster=ClusterSummary(**detail["cluster"]),
                images=detail["images"],
                image_count=detail["image_count"],
            ),
        )
    except ClusterNotFoundError:
        raise _not_found(cluster_id)
    except Exception as exc:
        logger.exception("Unexpected error fetching cluster %s", cluster_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False, error="Internal Error", message=str(exc)
            ).model_dump(),
        )


# ---------------------------------------------------------------------------
# PATCH /clusters/{cluster_id}  – Rename
# ---------------------------------------------------------------------------


@router.patch(
    "/{cluster_id}",
    response_model=RenameClusterResponse,
    responses=_ERR_RESPONSES,
    summary="Rename a manual cluster",
)
def rename_cluster_endpoint(cluster_id: str, body: RenameClusterRequest):
    """Rename an existing manual cluster."""
    try:
        updated = rename_cluster(cluster_id, body.name)
        return RenameClusterResponse(
            success=True,
            message=f"Cluster renamed to '{updated['name']}'.",
            data=ClusterSummary(**updated),
        )
    except ClusterNotFoundError:
        raise _not_found(cluster_id)
    except ValueError as exc:
        raise _bad_request(str(exc))
    except Exception as exc:
        logger.exception("Unexpected error renaming cluster %s", cluster_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False, error="Internal Error", message=str(exc)
            ).model_dump(),
        )


# ---------------------------------------------------------------------------
# DELETE /clusters/{cluster_id}  – Delete cluster
# ---------------------------------------------------------------------------


@router.delete(
    "/{cluster_id}",
    response_model=DeleteClusterResponse,
    responses=_ERR_RESPONSES,
    summary="Delete a manual cluster",
)
def delete_cluster_endpoint(cluster_id: str = Path(...)):
    """Delete a manual cluster and remove all its image assignments."""
    try:
        delete_cluster(cluster_id)
        return DeleteClusterResponse(
            success=True,
            message=f"Cluster '{cluster_id}' deleted.",
        )
    except ClusterNotFoundError:
        raise _not_found(cluster_id)
    except Exception as exc:
        logger.exception("Unexpected error deleting cluster %s", cluster_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False, error="Internal Error", message=str(exc)
            ).model_dump(),
        )


# ---------------------------------------------------------------------------
# POST /clusters/{cluster_id}/images  – Bulk assign
# ---------------------------------------------------------------------------


@router.post(
    "/{cluster_id}/images",
    response_model=AssignImagesResponse,
    responses=_ERR_RESPONSES,
    summary="Bulk-assign images to a cluster",
)
def assign_images_endpoint(cluster_id: str, body: AssignImagesRequest):
    """
    Assign one or more images to a manual cluster.

    - Already-assigned images are silently skipped (idempotent).
    - Returns HTTP 400 if any image_id does not exist.
    """
    try:
        result = assign_images(cluster_id, body.image_ids)
        return AssignImagesResponse(
            success=True,
            message=(
                f"{result['assigned_count']} image(s) assigned, "
                f"{result['skipped_count']} already present."
            ),
            **result,
        )
    except ClusterNotFoundError:
        raise _not_found(cluster_id)
    except ImageNotFoundError as exc:
        raise _bad_request(f"Image(s) not found: {exc.missing}")
    except ValueError as exc:
        raise _bad_request(str(exc))
    except Exception as exc:
        logger.exception("Unexpected error assigning images to cluster %s", cluster_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False, error="Internal Error", message=str(exc)
            ).model_dump(),
        )


# ---------------------------------------------------------------------------
# DELETE /clusters/{cluster_id}/images/{image_id}  – Remove single image
# ---------------------------------------------------------------------------


@router.delete(
    "/{cluster_id}/images/{image_id}",
    response_model=RemoveImageResponse,
    responses=_ERR_RESPONSES,
    summary="Remove an image from a cluster",
)
def remove_image_endpoint(cluster_id: str = Path(...), image_id: str = Path(...)):
    """Unassign a specific image from a manual cluster."""
    try:
        remove_image(cluster_id, image_id)
        return RemoveImageResponse(
            success=True,
            message=f"Image '{image_id}' removed from cluster '{cluster_id}'.",
        )
    except ClusterNotFoundError:
        raise _not_found(cluster_id)
    except ImageNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                success=False,
                error="Image Not In Cluster",
                message=f"Image '{image_id}' is not assigned to cluster '{cluster_id}'.",
            ).model_dump(),
        )
    except Exception as exc:
        logger.exception(
            "Unexpected error removing image %s from cluster %s", image_id, cluster_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False, error="Internal Error", message=str(exc)
            ).model_dump(),
        )
