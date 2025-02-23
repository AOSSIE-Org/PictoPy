from pydantic import BaseModel
from typing import Optional,List,Dict,Union

# Request Model

class TestRouteRequest(BaseModel):
    path: str  

class GetImagesRequest(BaseModel) : 
    pass

class AddSingleImageRequest(BaseModel) : 
    pass


# Response Model

class DetectionData(BaseModel):
    class_ids: List[int]  # List of detected class IDs
    detected_classes: List[str]  # List of class names

class TestRouteResponse(BaseModel):
    success: bool
    message: str
    data: DetectionData

class GetImagesResponse(BaseModel) : 
    pass 

class AddSingleImageResponse(BaseModel) : 
    pass

class ErrorResponse(BaseModel) :
    success: bool = False
    message: str
    error: str
