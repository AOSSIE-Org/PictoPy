from pydantic import BaseModel
from typing import Optional,List,Dict,Union

# Request Model

class RunGetClassesRequest(BaseModel) : 
    pass

class GetImagesRequest(BaseModel) : 
    pass

class AddSingleImageRequest(BaseModel) : 
    pass


# Response Model

class RunGetClassesResponse(BaseModel) : 
    pass 

class GetImagesResponse(BaseModel) : 
    pass 


class AddSingleImageResponse(BaseModel) : 
    pass

