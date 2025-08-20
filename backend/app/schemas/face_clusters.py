from pydantic import BaseModel
from typing import List, Optional


# Request Models
class RenameClusterRequest(BaseModel):
    cluster_name: str


# Response Models
class RenameClusterResponse(BaseModel):
    success: bool
    message: str
    cluster_id: str
    cluster_name: str


class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    error: str


class ClusterMetadata(BaseModel):
    cluster_id: str
    cluster_name: Optional[str]
    face_count: int


class GetClustersResponse(BaseModel):
    success: bool
    message: str
    clusters: List[ClusterMetadata]
