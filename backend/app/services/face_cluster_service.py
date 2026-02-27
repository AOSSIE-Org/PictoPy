from typing import Optional
from fastapi import HTTPException, status

from app.database.face_clusters import (
    db_get_cluster_by_id,
    db_update_cluster,
)
from app.schemas.face_clusters import (
    RenameClusterRequest,
    RenameClusterResponse,
    RenameClusterData,
)
from app.schemas.API import ErrorResponse


def rename_cluster_service(cluster_id: str, request: RenameClusterRequest) -> RenameClusterResponse:
    """
    Service layer for renaming a face cluster.
    Handles validation and business logic.
    """

    # Validation
    if not cluster_id.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                success=False,
                error="Validation Error",
                message="Cluster ID cannot be empty",
            ).model_dump(),
        )

    if not request.cluster_name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                success=False,
                error="Validation Error",
                message="Cluster name cannot be empty",
            ).model_dump(),
        )

    # Check existence
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

    # Update
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