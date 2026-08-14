from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from app.share.registry import PASSWORD_MAX_BYTES

# ##############################
# Request Handler
# ##############################


class CreateShareRequest(BaseModel):
    # None means the share lives until it is revoked or PictoPy closes.
    expires_in_minutes: Optional[int] = Field(default=None, gt=0)
    # None leaves the album readable by anyone holding the link.
    password: Optional[str] = Field(default=None, min_length=4)

    @field_validator("password")
    @classmethod
    def check_password_length(cls, value: Optional[str]) -> Optional[str]:
        # Measured in bytes because that is where bcrypt truncates; a longer
        # password would be accepted and then quietly not be the one set.
        if value is not None and len(value.encode("utf-8")) > PASSWORD_MAX_BYTES:
            raise ValueError(f"Password must be at most {PASSWORD_MAX_BYTES} bytes")
        return value


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
    # A 169.254 address only works when both devices sit on the same link, so
    # the picker can mark it as a last resort rather than a normal choice.
    is_link_local: bool


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
    # Whether a password stands between the link and the photos. The password
    # itself and its hash never leave the backend.
    is_protected: bool
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
