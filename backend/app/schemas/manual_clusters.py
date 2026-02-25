"""Pydantic schemas for the manual cluster endpoints."""

from __future__ import annotations

from typing import Any, List, Optional

from pydantic import BaseModel, field_validator


# ---------------------------------------------------------------------------
# Shared / reusable
# ---------------------------------------------------------------------------


class ErrorResponse(BaseModel):
    success: bool = False
    error: Optional[str] = None
    message: Optional[str] = None


# ---------------------------------------------------------------------------
# Request bodies
# ---------------------------------------------------------------------------


class CreateClusterRequest(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Cluster name must not be blank")
        return v.strip()


class RenameClusterRequest(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Cluster name must not be blank")
        return v.strip()


class AssignImagesRequest(BaseModel):
    image_ids: List[str]

    @field_validator("image_ids")
    @classmethod
    def must_not_be_empty(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("image_ids must contain at least one entry")
        return v


# ---------------------------------------------------------------------------
# Response data shapes
# ---------------------------------------------------------------------------


class ClusterSummary(BaseModel):
    cluster_id: str
    name: str
    created_at: str
    updated_at: str
    is_auto_generated: bool
    image_count: int = 0


class ImageInCluster(BaseModel):
    id: str
    path: str
    thumbnailPath: Optional[str] = None
    metadata: Optional[Any] = None


class ClusterDetail(BaseModel):
    cluster: ClusterSummary
    images: List[ImageInCluster]
    image_count: int


# ---------------------------------------------------------------------------
# Envelope responses
# ---------------------------------------------------------------------------


class CreateClusterResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    data: Optional[ClusterSummary] = None


class RenameClusterResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    data: Optional[ClusterSummary] = None


class GetAllClustersResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    data: Optional[List[ClusterSummary]] = None


class GetClusterDetailResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    data: Optional[ClusterDetail] = None


class AssignImagesResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    assigned_count: int = 0
    skipped_count: int = 0


class RemoveImageResponse(BaseModel):
    success: bool
    message: Optional[str] = None


class DeleteClusterResponse(BaseModel):
    success: bool
    message: Optional[str] = None
