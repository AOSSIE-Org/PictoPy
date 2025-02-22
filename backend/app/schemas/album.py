from pydantic import BaseModel,Field, field_validator
from typing import Optional,List
from pydantic_core.core_schema import ValidationInfo


# Request Handler
class AlbumCreate(BaseModel) :
    name : str
    description : Optional[str] = None
    is_hidden : bool = False
    password : Optional[str] = None

    @field_validator("password")
    def check_password(cls,value,info:ValidationInfo) :
        if info.data.get("is_hidden") and not value:
            raise ValueError("Password is required for hidden albums")
        return value


class AlbumDeleteRequest(BaseModel) : 
    name : str


class AddMultipleImagesRequest(BaseModel) :
    album_name: str
    paths: List[str]



# Response Handler

class AlbumCreateResponse(BaseModel) :
    success : bool
    message : str
    data : dict 

class AlbumDeleteResponse(BaseModel):
    success: bool
    message: str
    data: str | None = None  # Data can be None if an error occurs



class AddMultipleImagesResponse(BaseModel) : 
    success: bool
    message: str
    data: Optional[dict] = None



class ErrorResponse(BaseModel) :
    success: bool = False
    message: str
    error: str

