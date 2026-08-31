"""
User management router.

Protected endpoints for user profile management.
All endpoints require authentication.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.common import APIResponse
from app.schemas.user import ChangePasswordRequest, UserRead, UserUpdate
from app.services import user_service

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/me",
    response_model=APIResponse[UserRead],
    summary="Get current user profile",
)
async def get_profile(
    user: User = Depends(get_current_active_user),
):
    """Get the authenticated user's full profile."""
    return APIResponse(
        success=True,
        data=UserRead(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            avatar_url=user.avatar_url,
            auth_provider=user.auth_provider.value,
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at,
            updated_at=user.updated_at,
        ),
    )


@router.put(
    "/me",
    response_model=APIResponse[UserRead],
    summary="Update profile",
)
async def update_profile(
    update_data: UserUpdate,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Update the authenticated user's profile (name, avatar)."""
    updated_user = await user_service.update_user_profile(db, user, update_data)
    return APIResponse(
        success=True,
        data=UserRead(
            id=str(updated_user.id),
            email=updated_user.email,
            full_name=updated_user.full_name,
            avatar_url=updated_user.avatar_url,
            auth_provider=updated_user.auth_provider.value,
            is_active=updated_user.is_active,
            is_verified=updated_user.is_verified,
            created_at=updated_user.created_at,
            updated_at=updated_user.updated_at,
        ),
        message="Profile updated",
    )


@router.put(
    "/me/password",
    response_model=APIResponse,
    summary="Change password",
)
async def change_password(
    request: ChangePasswordRequest,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Change the authenticated user's password."""
    await user_service.change_user_password(
        db=db,
        user=user,
        current_password=request.current_password,
        new_password=request.new_password,
    )
    return APIResponse(success=True, message="Password changed successfully")
