from typing import List, Optional

from pydantic import BaseModel, Field

# ##############################
# Request Handler
# ##############################


class CreateShareRequest(BaseModel):
    # None means the share lives until it is revoked or PictoPy closes.
    expires_in_minutes: Optional[int] = Field(default=None, gt=0)


# ##############################
# Response Handler
# ##############################


class ShareInterface(BaseModel):
    """One address the share could be advertised on, best guess first."""

    interface: str
    ip: str
    is_default_route: bool
    looks_virtual: bool
    is_up: bool


class ShareUrl(BaseModel):
    interface: str
    ip: str
    url: str


class Share(BaseModel):
    token: str
    album_id: str
    album_name: str
    image_count: int
    port: int
    created_at: str
    expires_at: Optional[str] = None
    # One entry per candidate interface: which of them a phone can actually
    # reach depends on the network, so the caller picks.
    urls: List[ShareUrl]


class CreateShareResponse(BaseModel):
    success: bool
    message: str
    data: Share


class GetSharesResponse(BaseModel):
    success: bool
    data: List[Share]


class GetInterfacesResponse(BaseModel):
    success: bool
    data: List[ShareInterface]


class RevokeShareResponse(BaseModel):
    success: bool
    message: str


class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    error: str


# Named for this module rather than reusing the album schemas' generic name:
# two same-named models make FastAPI fall back to fully-qualified schema names
# in the generated OpenAPI, which would rename the album ones too.
class ShareErrorResponseEnvelope(BaseModel):
    """
    How an ErrorResponse actually reaches the client.

    HTTPException nests whatever it is given under `detail`, so documenting
    ErrorResponse alone would describe a shape no client ever receives.
    """

    detail: ErrorResponse
