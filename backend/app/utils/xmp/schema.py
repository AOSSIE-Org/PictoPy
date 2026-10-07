from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union

# Bump when a section's encoding changes incompatibly; readers skip newer data.
SCHEMA_VERSION = 1

BoundingBox = Dict[str, Union[int, float]]


@dataclass
class FaceRecord:
    embedding: List[float]
    bbox: Optional[BoundingBox] = None
    confidence: Optional[float] = None
    cluster_name: Optional[str] = None


@dataclass
class EmbeddingRecord:
    model_version: str
    vector: List[float]


@dataclass
class PictoPyMetadata:
    """Everything PictoPy derives for one image, independent of how it is stored."""

    schema_version: int = SCHEMA_VERSION
    tags: List[str] = field(default_factory=list)
    semantic_tags: List[str] = field(default_factory=list)
    faces: List[FaceRecord] = field(default_factory=list)
    image_embedding: Optional[EmbeddingRecord] = None
    favourite: Optional[bool] = None
    albums: List[str] = field(default_factory=list)
