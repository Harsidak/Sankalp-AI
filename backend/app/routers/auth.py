"""
Authentication router.

Handles registration, login, token refresh, Google OAuth, and logout.
All auth endpoints are public (no authentication required) except /me and /logout.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import (
    AuthUserResponse,
    GoogleAuthRequest,
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.common import APIResponse
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=APIResponse[TokenResponse],
    status_code=201,
    summary="Register a new account",
)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create a new account with email and password."""
    user, tokens = await auth_service.register(
        db=db,
        email=request.email,
        password=request.password,
        full_name=request.full_name,
    )
    return APIResponse(
        success=True,
        data=tokens,
        message="Account created successfully",
    )


@router.post(
    "/login",
    response_model=APIResponse[TokenResponse],
    summary="Login with email and password",
)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate with email and password, receive JWT tokens."""
    user, tokens = await auth_service.login(
        db=db,
        email=request.email,
        password=request.password,
    )
    return APIResponse(
        success=True,
        data=tokens,
        message="Login successful",
    )


@router.post(
    "/refresh",
    response_model=APIResponse[TokenResponse],
    summary="Refresh access token",
)
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """Exchange a valid refresh token for a new token pair (rotation)."""
    tokens = await auth_service.refresh_access_token(
        db=db,
        refresh_token_str=request.refresh_token,
    )
    return APIResponse(
        success=True,
        data=tokens,
        message="Token refreshed",
    )


@router.post(
    "/google",
    response_model=APIResponse[TokenResponse],
    summary="Google OAuth login",
)
async def google_auth(
    request: GoogleAuthRequest,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate via Google OAuth (authorization code or ID token)."""
    user, tokens = await auth_service.google_oauth(
        db=db,
        code=request.code,
        id_token=request.id_token,
        redirect_uri=request.redirect_uri,
    )
    return APIResponse(
        success=True,
        data=tokens,
        message="Google authentication successful",
    )


@router.get(
    "/me",
    response_model=APIResponse[AuthUserResponse],
    summary="Get current user",
)
async def get_me(user: User = Depends(get_current_user)):
    """Get the currently authenticated user's information."""
    return APIResponse(
        success=True,
        data=AuthUserResponse(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            avatar_url=user.avatar_url,
            auth_provider=user.auth_provider.value,
            is_verified=user.is_verified,
        ),
    )


@router.post(
    "/logout",
    response_model=APIResponse,
    summary="Logout",
)
async def logout(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Logout by revoking the refresh token."""
    await auth_service.logout(db=db, refresh_token_str=request.refresh_token)
    return APIResponse(success=True, message="Logged out successfully")
