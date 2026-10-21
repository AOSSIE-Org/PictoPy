from pydantic import BaseModel


class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    error: str
