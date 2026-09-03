"""
Authentication service: registration, login, token management, Google OAuth.

Handles the full auth lifecycle:
- Email/password registration and login
- JWT access/refresh token creation and rotation
- Google OAuth code exchange and account creation/linking
- Logout with token revocation
"""

import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.exceptions import AuthenticationError, ConflictError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
    verify_token_type,
)
from app.models.user import AuthProvider, RefreshToken, User
from app.schemas.auth import TokenResponse
from app.services import user_service

settings = get_settings()


def _hash_token(token: str) -> str:
    """Hash a refresh token for secure storage."""
    return hashlib.sha256(token.encode()).hexdigest()


def _as_utc(value: datetime) -> datetime:
    """
    Read a stored timestamp back as timezone-aware UTC.

    MySQL's DATETIME carries no offset, so a column declared
    `DateTime(timezone=True)` still hands back a *naive* datetime -- and the
    same is true of SQLite. Everything is written as UTC, so attaching the
    offset on read is correct rather than a guess.

    Without this, comparing a freshly-loaded expiry against
    `datetime.now(timezone.utc)` raises "can't compare offset-naive and
    offset-aware datetimes". The bug hid in tests because a token created
    and checked inside one session is served from the identity map with the
    original aware value; only a fresh request, which re-reads the row, hits
    the naive one.
    """
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def _create_token_pair(user_id: str) -> TokenResponse:
    """Generate an access/refresh token pair for a user."""
    access_token = create_access_token(data={"sub": str(user_id)})
    refresh_token = create_refresh_token(data={"sub": str(user_id)})
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.access_token_expire_minutes * 60,
    )


async def register(
    db: AsyncSession,
    email: str,
    password: str,
    full_name: Optional[str] = None,
) -> tuple[User, TokenResponse]:
    """
    Register a new user with email and password.

    Returns:
        Tuple of (created User, token pair).

    Raises:
        ConflictError: If email already exists.
    """
    user = await user_service.create_user(
        db=db,
        email=email,
        password=password,
        full_name=full_name,
        auth_provider=AuthProvider.LOCAL,
    )

    tokens = _create_token_pair(str(user.id))

    # Store refresh token hash in DB
    await _store_refresh_token(db, user.id, tokens.refresh_token)

    return user, tokens


async def login(
    db: AsyncSession,
    email: str,
    password: str,
) -> tuple[User, TokenResponse]:
    """
    Authenticate with email and password.

    Returns:
        Tuple of (authenticated User, token pair).

    Raises:
        AuthenticationError: If credentials are invalid.
    """
    user = await user_service.get_user_by_email(db, email)

    if not user:
        raise AuthenticationError("Invalid email or password")

    if not user.hashed_password:
        raise AuthenticationError(
            "This account uses Google sign-in. Please log in with Google."
        )

    if not verify_password(password, user.hashed_password):
        raise AuthenticationError("Invalid email or password")

    if not user.is_active:
        raise AuthenticationError("Account is deactivated")

    tokens = _create_token_pair(str(user.id))
    await _store_refresh_token(db, user.id, tokens.refresh_token)

    return user, tokens


async def refresh_access_token(
    db: AsyncSession,
    refresh_token_str: str,
) -> TokenResponse:
    """
    Refresh an access token using a valid refresh token.

    Implements token rotation: the old refresh token is revoked
    and a new pair is issued.

    Returns:
        New token pair.

    Raises:
        AuthenticationError: If refresh token is invalid or revoked.
    """
    # Verify the JWT
    payload = verify_token_type(refresh_token_str, "refresh")
    if not payload:
        raise AuthenticationError("Invalid or expired refresh token")

    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationError("Invalid token payload")

    # Check the token hash in DB
    token_hash = _hash_token(refresh_token_str)
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.is_revoked == False,  # noqa: E712
        )
    )
    stored_token = result.scalar_one_or_none()

    if not stored_token:
        raise AuthenticationError("Refresh token has been revoked")

    if _as_utc(stored_token.expires_at) < datetime.now(timezone.utc):
        raise AuthenticationError("Refresh token has expired")

    # Rotate: revoke old token, issue new pair
    stored_token.is_revoked = True

    new_tokens = _create_token_pair(user_id)
    await _store_refresh_token(db, UUID(user_id), new_tokens.refresh_token)

    return new_tokens


async def google_oauth(
    db: AsyncSession,
    code: Optional[str] = None,
    id_token: Optional[str] = None,
    redirect_uri: Optional[str] = None,
) -> tuple[User, TokenResponse]:
    """
    Authenticate via Google OAuth.

    Supports two flows:
    1. Authorization code flow: exchange code for tokens, get user info
    2. ID token flow: verify ID token directly (frontend-initiated)

    Creates a new account if the Google user doesn't exist,
    or links/logs into an existing account.

    Returns:
        Tuple of (User, token pair).

    Raises:
        AuthenticationError: If OAuth flow fails.
    """
    if code:
        google_user = await _exchange_google_code(code, redirect_uri)
    elif id_token:
        google_user = await _verify_google_id_token(id_token)
    else:
        raise AuthenticationError("Either 'code' or 'id_token' is required")

    google_id = google_user["sub"]
    email = google_user.get("email")
    full_name = google_user.get("name")
    avatar_url = google_user.get("picture")

    if not email:
        raise AuthenticationError("Google account does not have an email")

    # Check if user exists by Google ID
    user = await user_service.get_user_by_google_id(db, google_id)

    if not user:
        # Check if user exists by email (link accounts)
        user = await user_service.get_user_by_email(db, email)
        if user:
            # Link Google to existing account
            await user_service.link_google_account(db, user, google_id, avatar_url)
        else:
            # Create new account
            user = await user_service.create_user(
                db=db,
                email=email,
                full_name=full_name,
                avatar_url=avatar_url,
                auth_provider=AuthProvider.GOOGLE,
                google_id=google_id,
                is_verified=True,  # Google emails are verified
            )

    tokens = _create_token_pair(str(user.id))
    await _store_refresh_token(db, user.id, tokens.refresh_token)

    return user, tokens


async def logout(db: AsyncSession, refresh_token_str: str) -> None:
    """
    Logout by revoking the refresh token.
    The access token will expire naturally (short-lived).
    """
    token_hash = _hash_token(refresh_token_str)
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    stored_token = result.scalar_one_or_none()
    if stored_token:
        stored_token.is_revoked = True


async def revoke_all_tokens(db: AsyncSession, user_id: UUID) -> None:
    """Revoke all refresh tokens for a user (e.g., password change, security event)."""
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.is_revoked == False,  # noqa: E712
        )
    )
    tokens = result.scalars().all()
    for token in tokens:
        token.is_revoked = True


# =============================================================================
# Internal helpers
# =============================================================================

async def _store_refresh_token(
    db: AsyncSession,
    user_id: UUID,
    refresh_token: str,
) -> RefreshToken:
    """Store a hashed refresh token in the database."""
    token_hash = _hash_token(refresh_token)
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)

    stored_token = RefreshToken(
        token_hash=token_hash,
        user_id=user_id,
        expires_at=expires_at,
    )
    db.add(stored_token)
    await db.flush()
    return stored_token


async def _exchange_google_code(
    code: str,
    redirect_uri: Optional[str] = None,
) -> dict:
    """Exchange Google authorization code for user info."""
    token_url = "https://oauth2.googleapis.com/token"
    userinfo_url = "https://www.googleapis.com/oauth2/v3/userinfo"

    async with httpx.AsyncClient() as client:
        # Exchange code for access token
        token_response = await client.post(
            token_url,
            data={
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri or settings.google_redirect_uri,
            },
        )

        if token_response.status_code != 200:
            raise AuthenticationError("Failed to exchange Google authorization code")

        token_data = token_response.json()
        access_token = token_data.get("access_token")

        # Fetch user info
        userinfo_response = await client.get(
            userinfo_url,
            headers={"Authorization": f"Bearer {access_token}"},
        )

        if userinfo_response.status_code != 200:
            raise AuthenticationError("Failed to fetch Google user info")

        return userinfo_response.json()


async def _verify_google_id_token(id_token: str) -> dict:
    """Verify a Google ID token and extract user info."""
    verify_url = f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}"

    async with httpx.AsyncClient() as client:
        response = await client.get(verify_url)

        if response.status_code != 200:
            raise AuthenticationError("Invalid Google ID token")

        data = response.json()

        # Verify the token was issued for our app
        if data.get("aud") != settings.google_client_id:
            raise AuthenticationError("Google ID token was not issued for this application")

        return data
