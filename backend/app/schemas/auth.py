"""
Authentication request/response schemas.
"""

from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    """Email/password registration."""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: Optional[str] = Field(None, max_length=255)


class LoginRequest(BaseModel):
    """Email/password login."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """JWT token pair returned after successful authentication."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Access token expiry in seconds")


class RefreshTokenRequest(BaseModel):
    """Request to refresh an access token using a refresh token."""
    refresh_token: str


class GoogleAuthRequest(BaseModel):
    """Google OAuth callback with authorization code or ID token."""
    code: Optional[str] = None  # Authorization code flow
    id_token: Optional[str] = None  # Implicit flow (frontend sends ID token directly)
    redirect_uri: Optional[str] = None


class AuthUserResponse(BaseModel):
    """Current authenticated user info."""
    id: str
    email: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    auth_provider: str
    is_verified: bool

    class Config:
        from_attributes = True
