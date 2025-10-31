from pydantic import BaseModel
from typing import List, Optional, Dict, Union, Any


# Request Models
class RenameClusterRequest(BaseModel):
    cluster_name: str


# Response Models
class RenameClusterData(BaseModel):
    cluster_id: str
    cluster_name: str


class RenameClusterResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
    data: Optional[RenameClusterData] = None


class ErrorResponse(BaseModel):
    success: bool = False
    message: Optional[str] = None
    error: Optional[str] = None


class ClusterMetadata(BaseModel):
    cluster_id: str
    cluster_name: Optional[str]
    face_image_base64: Optional[str]
    face_count: int


class GetClustersData(BaseModel):
    clusters: List[ClusterMetadata]


class GetClustersResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
    data: Optional[GetClustersData] = None


class ImageInCluster(BaseModel):
    """Represents an image that contains faces from a specific cluster."""

    id: str
    path: str
    thumbnailPath: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    face_id: int
    confidence: Optional[float] = None
    bbox: Optional[Dict[str, Union[int, float]]] = None


class GetClusterImagesData(BaseModel):
    """Data model for cluster images response."""

    cluster_id: str
    cluster_name: Optional[str] = None
    images: List[ImageInCluster]
    total_images: int


class GetClusterImagesResponse(BaseModel):
    """Response model for getting images in a cluster."""

    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
    data: Optional[GetClusterImagesData] = None


class GlobalReclusterData(BaseModel):
    clusters_created: Optional[int] = None


class GlobalReclusterResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
    data: Optional[GlobalReclusterData] = None
