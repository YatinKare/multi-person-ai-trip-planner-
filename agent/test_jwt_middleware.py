"""
Unit tests for JWT middleware.
Run with: uv run python test_jwt_middleware.py
"""

from api.middleware.auth import decode_token, TokenData
from jose import jwt
import os
from datetime import datetime, timedelta

def test_jwt_middleware():
    """Test JWT token decoding functionality."""

    # Get JWT secret from environment
    jwt_secret = os.getenv("SUPABASE_JWT_SECRET")
    assert jwt_secret, "SUPABASE_JWT_SECRET not loaded"
    print(f"✓ JWT_SECRET loaded from environment")

    # Create a test token (simulating what Supabase would send)
    test_user_id = "123e4567-e89b-12d3-a456-426614174000"
    test_email = "test@example.com"
    test_role = "authenticated"

    # Create token payload
    payload = {
        "sub": test_user_id,
        "email": test_email,
        "role": test_role,
        "aud": "authenticated",
        "exp": datetime.utcnow() + timedelta(hours=1),
        "iat": datetime.utcnow()
    }

    # Encode token
    test_token = jwt.encode(payload, jwt_secret, algorithm="HS256")
    print(f"✓ Created test JWT token")

    # Test decode_token function
    try:
        token_data = decode_token(test_token)
        assert isinstance(token_data, TokenData)
        assert token_data.user_id == test_user_id
        assert token_data.email == test_email
        assert token_data.role == test_role
        print(f"✓ decode_token() correctly extracts user data")
        print(f"  - user_id: {token_data.user_id}")
        print(f"  - email: {token_data.email}")
        print(f"  - role: {token_data.role}")
    except Exception as e:
        print(f"✗ decode_token() failed: {e}")
        return False

    # Test with expired token
    expired_payload = {
        "sub": test_user_id,
        "exp": datetime.utcnow() - timedelta(hours=1),  # Expired 1 hour ago
        "iat": datetime.utcnow() - timedelta(hours=2)
    }
    expired_token = jwt.encode(expired_payload, jwt_secret, algorithm="HS256")

    try:
        decode_token(expired_token)
        print(f"✗ decode_token() should have rejected expired token")
        return False
    except Exception:
        print(f"✓ decode_token() correctly rejects expired tokens")

    # Test with invalid token
    try:
        decode_token("invalid.token.here")
        print(f"✗ decode_token() should have rejected invalid token")
        return False
    except Exception:
        print(f"✓ decode_token() correctly rejects invalid tokens")

    # Test with token missing user ID
    no_sub_payload = {
        "email": test_email,
        "exp": datetime.utcnow() + timedelta(hours=1),
        "iat": datetime.utcnow()
    }
    no_sub_token = jwt.encode(no_sub_payload, jwt_secret, algorithm="HS256")

    try:
        decode_token(no_sub_token)
        print(f"✗ decode_token() should have rejected token without user ID")
        return False
    except Exception:
        print(f"✓ decode_token() correctly rejects tokens without user ID")

    print(f"\n✅ All JWT middleware tests passed!")
    return True


if __name__ == "__main__":
    success = test_jwt_middleware()
    exit(0 if success else 1)
