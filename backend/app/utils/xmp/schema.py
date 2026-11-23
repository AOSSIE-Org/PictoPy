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
class SemanticTag:
    name: str
    # Kept so a reader can rebuild the display cut and search thresholds.
    score: float


@dataclass
class EmbeddingRecord:
    model_version: str
    vector: List[float]


@dataclass
class PictoPyMetadata:
    """Everything PictoPy derives for one image, independent of how it is stored."""

    schema_version: int = SCHEMA_VERSION
    tags: List[str] = field(default_factory=list)
    semantic_tags: List[SemanticTag] = field(default_factory=list)
    faces: List[FaceRecord] = field(default_factory=list)
    image_embedding: Optional[EmbeddingRecord] = None
    favourite: Optional[bool] = None
    albums: List[str] = field(default_factory=list)
    # Which models/vocabulary produced the data, so a reader can tell whether
    # it is still safe to reuse.
    models: Dict[str, str] = field(default_factory=dict)
    # Lets a reader notice the pixels were cropped or resized since export.
    width: Optional[int] = None
    height: Optional[int] = None
