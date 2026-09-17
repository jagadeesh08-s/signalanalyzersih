"""
Authentication utilities for API key and JWT token authentication.
"""
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

from app.core.config import settings

# API Key header
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# Bearer token
bearer_scheme = HTTPBearer(auto_error=False)


async def get_api_key(api_key: str = Security(api_key_header)) -> str:
    """Validate API key from header."""
    if not settings.ENABLE_AUTH:
        return "development"
    
    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    if api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    return api_key


async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme)) -> str:
    """Validate JWT token (placeholder for future JWT auth)."""
    if not settings.ENABLE_AUTH:
        return "development"
    
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # TODO: Implement JWT validation
    return credentials.credentials


# Combined dependency - use either API key or JWT
async def authenticate(api_key: str = Depends(get_api_key)) -> str:
    """Authenticate using API key or JWT token."""
    return api_key


# Optional authentication - for endpoints that work with or without auth
async def optional_auth(api_key: str = Security(api_key_header)) -> Optional[str]:
    """Optional authentication - returns None if not authenticated."""
    if not settings.ENABLE_AUTH:
        return "development"
    
    if api_key is None or api_key != settings.API_KEY:
        return None
    
    return api_key