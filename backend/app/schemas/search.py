"""
Pydantic schemas for the semantic search API.
"""

from typing import List
from pydantic import BaseModel, Field


class SearchResultItem(BaseModel):
    """A single ranked result from a semantic search query."""

    image_id: str = Field(..., description="UUID of the matched image.")
    score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Cosine similarity score in [0, 1]; higher is more relevant.",
    )
    path: str = Field(..., description="Absolute filesystem path to the image.")
    thumbnail_path: str = Field(
        ..., description="Absolute path to the pre-generated thumbnail."
    )
    tags: List[str] = Field(
        default_factory=list,
        description="YOLO object-class tags detected in the image.",
    )


class SemanticSearchResponse(BaseModel):
    """Successful response from ``GET /search/semantic``."""

    success: bool = True
    query: str = Field(..., description="The query string that was searched.")
    total: int = Field(..., description="Number of results returned.")
    results: List[SearchResultItem]


class IndexStatusResponse(BaseModel):
    """Response from ``GET /search/index-status``."""

    success: bool = True
    indexed_count: int = Field(
        ..., description="Number of images currently in the semantic index."
    )
    is_loaded: bool = Field(
        ...,
        description="Whether the in-memory index has been loaded from the database.",
    )


class IndexTriggerResponse(BaseModel):
    """Response from ``POST /search/index``."""

    success: bool = True
    message: str
    newly_indexed: int = Field(
        ..., description="Number of images indexed during this call."
    )
