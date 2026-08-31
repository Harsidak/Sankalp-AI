"""
User management request/response schemas.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    """Admin-level user creation (includes all fields)."""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: Optional[str] = Field(None, max_length=255)
    is_active: bool = True
    is_verified: bool = False


class UserRead(BaseModel):
    """Public user profile response."""
    id: str
    email: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    auth_provider: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """User profile update (partial)."""
    full_name: Optional[str] = Field(None, max_length=255)
    avatar_url: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    """Password change request (requires current password)."""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)
