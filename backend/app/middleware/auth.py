"""
Authentication middleware for PictoPy API.
Supports both JWT tokens and API key authentication.
"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

from app.config.settings import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, API_KEY

# Security schemes
security = HTTPBearer(auto_error=False)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Data to encode in the token
        expires_delta: Token expiration time
        
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> dict:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token to verify
        
    Returns:
        Decoded token payload
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def verify_api_key(x_api_key: Optional[str] = Header(None)) -> bool:
    """
    Verify API key from header for Tauri application.
    
    Args:
        x_api_key: API key from X-API-Key header
        
    Returns:
        True if API key is valid
        
    Raises:
        HTTPException: If API key is invalid or missing
    """
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is missing",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    if x_api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
        )
    
    return True


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    x_api_key: Optional[str] = Header(None),
) -> Optional[dict]:
    """
    Get current user from JWT token or API key (optional authentication).
    Used for endpoints that work with or without authentication.
    
    Args:
        credentials: HTTP Bearer credentials
        x_api_key: API key from header
        
    Returns:
        User data if authenticated, None otherwise
    """
    # Check API key first (for Tauri app)
    if x_api_key and x_api_key == API_KEY:
        return {"authenticated_via": "api_key", "client": "tauri"}
    
    # Check JWT token
    if credentials and credentials.credentials:
        try:
            payload = verify_token(credentials.credentials)
            return payload
        except HTTPException:
            return None
    
    return None


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    x_api_key: Optional[str] = Header(None),
) -> dict:
    """
    Get current user from JWT token or API key (required authentication).
    Used for protected endpoints that require authentication.
    
    Args:
        credentials: HTTP Bearer credentials
        x_api_key: API key from header
        
    Returns:
        User data
        
    Raises:
        HTTPException: If authentication fails
    """
    # Check API key first (for Tauri app)
    if x_api_key and x_api_key == API_KEY:
        return {"authenticated_via": "api_key", "client": "tauri"}
    
    # Check JWT token
    if credentials and credentials.credentials:
        payload = verify_token(credentials.credentials)
        return payload
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )
