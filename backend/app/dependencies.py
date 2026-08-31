"""
FastAPI dependency injection functions.

These are injected into route handlers via Depends().
They provide database sessions, authenticated user objects,
and service instances to routes without coupling.
"""

from typing import Optional
from uuid import UUID

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.database import get_db
from app.core.exceptions import AuthenticationError
from app.core.security import verify_token_type
from app.models.user import User
from app.services import user_service

settings = get_settings()


async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Extract and validate the JWT from the Authorization header.
    Returns the authenticated User object.

    Usage in routes:
        @router.get("/protected")
        async def protected(user: User = Depends(get_current_user)):
            ...

    Raises:
        AuthenticationError: If token is missing, invalid, or user not found.
    """
    if not authorization:
        raise AuthenticationError("Authorization header is required")

    # Extract token from "Bearer <token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise AuthenticationError("Invalid authorization header format. Use: Bearer <token>")

    token = parts[1]

    # Decode and validate
    payload = verify_token_type(token, "access")
    if not payload:
        raise AuthenticationError("Invalid or expired access token")

    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationError("Invalid token payload")

    # Fetch user from DB
    try:
        user = await user_service.get_user_by_id(db, UUID(user_id))
    except (ValueError, TypeError):
        raise AuthenticationError("Invalid user ID in token")

    if not user:
        raise AuthenticationError("User not found")

    return user


async def get_current_active_user(
    user: User = Depends(get_current_user),
) -> User:
    """
    Same as get_current_user but also checks that the user is active.
    Use this for routes that require an active (non-deactivated) account.

    Raises:
        AuthenticationError: If user account is deactivated.
    """
    if not user.is_active:
        raise AuthenticationError("Account is deactivated")
    return user


async def get_optional_user(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """
    Optional authentication — returns User if valid token present, None otherwise.
    Use this for routes that work both authenticated and unauthenticated
    (e.g., landing page with personalized content).
    """
    if not authorization:
        return None

    try:
        return await get_current_user(authorization, db)
    except AuthenticationError:
        return None
