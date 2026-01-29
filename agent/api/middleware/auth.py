"""JWT authentication middleware for validating Supabase tokens."""

import os
from pathlib import Path
from typing import Optional
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables from project root
# Navigate up from agent/api/middleware/auth.py to project root
project_root = Path(__file__).parent.parent.parent.parent
env_file = project_root / ".env.local"
load_dotenv(env_file)


class TokenData(BaseModel):
    """Decoded JWT token data."""
    user_id: str
    email: Optional[str] = None
    role: Optional[str] = None


# HTTP Bearer token security scheme
security = HTTPBearer()

# Get JWT secret from environment
JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")
if not JWT_SECRET:
    raise RuntimeError("SUPABASE_JWT_SECRET environment variable is required")

# JWT algorithm (Supabase uses HS256)
ALGORITHM = "HS256"


def decode_token(token: str) -> TokenData:
    """
    Decode and validate a JWT token.

    Args:
        token: JWT token string

    Returns:
        TokenData with user_id and other claims

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        # Decode the JWT token
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[ALGORITHM],
            options={"verify_aud": False}  # Supabase tokens don't always have aud
        )

        # Extract user ID (Supabase uses 'sub' claim for user ID)
        user_id: str = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Extract optional claims
        email = payload.get("email")
        role = payload.get("role")

        return TokenData(user_id=user_id, email=email, role=role)

    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> TokenData:
    """
    FastAPI dependency to extract and validate user from JWT token.

    Usage in route:
        @router.get("/protected")
        async def protected_route(user: TokenData = Depends(get_current_user)):
            return {"user_id": user.user_id}

    Args:
        credentials: HTTP Authorization credentials from request header

    Returns:
        TokenData with validated user information

    Raises:
        HTTPException: If token is missing, invalid, or expired
    """
    token = credentials.credentials
    return decode_token(token)


async def get_current_user_optional(
    authorization: Optional[str] = None
) -> Optional[TokenData]:
    """
    FastAPI dependency for optional authentication.
    Returns None if no token provided, validates if present.

    Usage in route:
        from fastapi import Header
        @router.get("/public-or-private")
        async def mixed_route(
            user: Optional[TokenData] = Depends(get_current_user_optional),
            authorization: Optional[str] = Header(None)
        ):
            if user:
                return {"message": f"Hello {user.user_id}"}
            return {"message": "Hello anonymous"}

    Args:
        authorization: Optional Authorization header value

    Returns:
        TokenData if token is valid, None if no token provided

    Raises:
        HTTPException: If token is provided but invalid
    """
    if not authorization:
        return None

    # Extract token from "Bearer <token>" format
    if not authorization.startswith("Bearer "):
        return None

    token = authorization.replace("Bearer ", "")
    return decode_token(token)
