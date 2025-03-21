from pydantic import BaseModel
from typing import List, Dict

# Response Model
class SimilarPair(BaseModel):
    image1: str
    image2: str
    similarity: float


class FaceMatchingResponse(BaseModel):
    success: bool
    message: str
    similar_pairs: List[SimilarPair]


class FaceClustersResponse(BaseModel):
    success: bool
    message: str
    clusters: Dict[int, List[str]]


class GetRelatedImagesResponse(BaseModel):
    success: bool
    message: str
    data: Dict[str, List[str]]


class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    error: str
