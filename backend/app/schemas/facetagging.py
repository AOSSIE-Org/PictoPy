from pydantic import BaseModel
from typing import Optional,List,Dict,Union


# Request Model 
class FaceMatchingRequest(BaseModel) : 
    pass 

class FaceClustersRequest(BaseModel) : 
    pass

class GetRelatedImagesRequest(BaseModel) : 
    pass

# Response Model 
class FaceMatchingResponse(BaseModel) : 
    pass

class FaceClustersResponse(BaseModel) : 
    pass

class GetRelatedImagesResponse(BaseModel) : 
    pass