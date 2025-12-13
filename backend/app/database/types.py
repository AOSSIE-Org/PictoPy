"""Type definitions for database operations."""
from typing import TypedDict, Optional, List, Any
from datetime import datetime


class ImageRow(TypedDict, total=False):
    """Type definition for image database row."""
    id: int
    path: str
    thumbnail_path: Optional[str]
    folder_id: str
    metadata: Optional[str]  # JSON string
    created_at: str
    updated_at: str


class FolderRow(TypedDict, total=False):
    """Type definition for folder database row."""
    id: str
    path: str
    name: str
    ai_tagging_enabled: int  # SQLite boolean (0 or 1)
    created_at: str
    updated_at: str


class FaceClusterRow(TypedDict, total=False):
    """Type definition for face cluster database row."""
    id: int
    cluster_label: int
    name: Optional[str]
    representative_face_id: Optional[int]
    created_at: str
    updated_at: str


class TagRow(TypedDict, total=False):
    """Type definition for tag database row."""
    id: int
    image_id: int
    tag_name: str
    confidence: float
    created_at: str


class MetadataDict(TypedDict, total=False):
    """Type definition for parsed image metadata."""
    camera: Optional[str]
    location: Optional[str]
    date_taken: Optional[str]
    width: Optional[int]
    height: Optional[int]
    file_size: Optional[int]
    format: Optional[str]
