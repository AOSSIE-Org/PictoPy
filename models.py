from pydantic import BaseModel, Field
from typing import List
from uuid import uuid4


class Photo(BaseModel):
    id: str
    url: str
    tags: List[str] = []
    faces: int = 0


class SmartAlbum(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    type: str  # 'object', 'face', or 'manual'
    photos: List[str] = []  # list of photo ids
    auto_update: bool = False
