"""
Authentication routes for PictoPy API.
"""

from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, status, Header
from pydantic import BaseModel

from app.middleware.auth import create_access_token, verify_api_key
from app.config.settings import ACCESS_TOKEN_EXPIRE_MINUTES, API_KEY

router = APIRouter()


class TokenRequest(BaseModel):
    """Request model for token generation."""

    client_id: str
    api_key: str


class TokenResponse(BaseModel):
    """Response model for token generation."""

    access_token: str
    token_type: str
    expires_in: int


class AuthStatusResponse(BaseModel):
    """Response model for auth status check."""

    authenticated: bool
    auth_method: Optional[str] = None
    message: str


@router.post(
    "/token",
    response_model=TokenResponse,
    summary="Generate JWT Token",
    description="Generate a JWT access token using API key authentication. Used for testing or future web interface.",
)
async def generate_token(request: TokenRequest):
    """
    Generate a JWT access token.

    Args:
        request: Token request containing client_id and api_key

    Returns:
        Access token and expiration info

    Raises:
        HTTPException: If API key is invalid
    """
    # Verify API key
    if request.api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
        )

    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": request.client_id, "client": "web"}, expires_delta=access_token_expires
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # in seconds
    )


@router.get(
    "/status",
    response_model=AuthStatusResponse,
    summary="Check Authentication Status",
    description="Check if the provided API key is valid.",
)
async def check_auth_status(x_api_key: Optional[str] = Header(None)):
    """
    Check authentication status.

    Args:
        x_api_key: API key from X-API-Key header

    Returns:
        Authentication status
    """
    if x_api_key and x_api_key == API_KEY:
        return AuthStatusResponse(
            authenticated=True,
            auth_method="api_key",
            message="Successfully authenticated via API key",
        )

    return AuthStatusResponse(
        authenticated=False, auth_method=None, message="Not authenticated"
    )
