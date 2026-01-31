"""JWT authentication middleware for validating Supabase tokens."""

import os
from typing import Optional
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from api.database import get_supabase_client

class TokenData(BaseModel):
    """Decoded JWT token data."""
    user_id: str
    email: Optional[str] = None
    role: Optional[str] = None


# HTTP Bearer token security scheme
security = HTTPBearer()


def verify_token(token: str) -> TokenData:
    """
    Verify a token using Supabase Auth API.
    
    This replaces local JWT verification to avoid issues with
    key formats (ES256 vs HS256) and public key management.
    Validates against the Supabase Auth server.

    Args:
        token: JWT token string

    Returns:
        TokenData with user_id and other claims

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        supabase = get_supabase_client()
        
        # Verify token by fetching user details from Supabase Auth
        # This checks signatures, expiry, and revocation
        user_response = supabase.auth.get_user(token)
        user = user_response.user
        
        if not user or not user.id:
             raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: user not found",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return TokenData(
            user_id=user.id,
            email=user.email,
            role=user.role
        )

    except Exception as e:
        # Catch errors (including network issues, invalid tokens, or client config)
        print(f"Auth verification error: {e}")
        error_msg = str(e)
        if "Invalid token" in error_msg or "expired" in error_msg:
             raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid or expired token: {error_msg}",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> TokenData:
    """
    FastAPI dependency to extract and validate user from JWT token.

    Args:
        credentials: HTTP Authorization credentials from request header

    Returns:
        TokenData with validated user information
    """
    token = credentials.credentials
    return verify_token(token)


async def get_current_user_optional(
    authorization: Optional[str] = None
) -> Optional[TokenData]:
    """
    FastAPI dependency for optional authentication.
    Returns None if no token provided, validates if present.

    Args:
        authorization: Optional Authorization header value

    Returns:
        TokenData if token is valid, None if no token provided
    """
    if not authorization:
        return None

    # Extract token from "Bearer <token>" format
    if not authorization.startswith("Bearer "):
        return None

    token = authorization.replace("Bearer ", "")
    return verify_token(token)
