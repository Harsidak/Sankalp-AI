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
from app.schemas.account import (
    AccountExport,
    DeleteAccountRequest,
    DeleteAccountResult,
)
from app.schemas.common import APIResponse
from app.schemas.user import ChangePasswordRequest, UserRead, UserUpdate
from app.services import account_service, user_service

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


@router.get(
    "/me/export",
    response_model=APIResponse[AccountExport],
    summary="Export every row this account owns",
)
async def export_account(
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    The whole account as one JSON document: check-ins, journal entries with
    their tags, habits with their completed dates, and the tag list.

    `counts` carries the row total per table so the export can be checked
    against the database at a glance.
    """
    export = await account_service.export_account(db, user)
    return APIResponse(success=True, data=export)


@router.delete(
    "/me",
    response_model=APIResponse[DeleteAccountResult],
    summary="Delete the account and all of its data",
)
async def delete_account(
    data: DeleteAccountRequest,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Permanently delete the account. This cannot be undone.

    Deleting the user row is the entire operation: every wellness table
    declares ON DELETE CASCADE against users.id, so the database removes
    the dependent rows itself. The response reports what went with it,
    counted immediately before the delete.
    """
    removed = await account_service.delete_account(db, user, data)
    return APIResponse(
        success=True,
        data=DeleteAccountResult(deleted=True, removed=removed),
        message="Account deleted",
    )
