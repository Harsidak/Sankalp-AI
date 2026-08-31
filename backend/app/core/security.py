"""
Security utilities: password hashing and JWT token management.

Uses bcrypt for password hashing and python-jose for JWT encoding/decoding.
Tokens carry a 'type' claim to distinguish access vs refresh tokens.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import get_settings

settings = get_settings()

# Password hashing context — bcrypt with auto-upgrade support
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    data: dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a short-lived JWT access token.

    Args:
        data: Payload to encode (must include 'sub' with user ID).
        expires_delta: Custom expiry. Defaults to ACCESS_TOKEN_EXPIRE_MINUTES.

    Returns:
        Encoded JWT string.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access",
    })
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(
    data: dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a long-lived JWT refresh token.

    Args:
        data: Payload to encode (must include 'sub' with user ID).
        expires_delta: Custom expiry. Defaults to REFRESH_TOKEN_EXPIRE_DAYS.

    Returns:
        Encoded JWT string.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(days=settings.refresh_token_expire_days)
    )
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh",
    })
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> Optional[dict[str, Any]]:
    """
    Decode and validate a JWT token.

    Returns:
        Decoded payload dict if valid, None if invalid/expired.
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except JWTError:
        return None


def verify_token_type(token: str, expected_type: str) -> Optional[dict[str, Any]]:
    """
    Decode a token and verify its type claim matches expected_type.

    Args:
        token: JWT string.
        expected_type: Expected 'type' claim ('access' or 'refresh').

    Returns:
        Decoded payload if valid and correct type, None otherwise.
    """
    payload = decode_token(token)
    if payload is None:
        return None
    if payload.get("type") != expected_type:
        return None
    return payload
