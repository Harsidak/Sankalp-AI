"""
User service: CRUD operations and profile management.

All database operations for users are encapsulated here.
Routers call service methods — they never touch the DB directly.
"""

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.core.security import hash_password, verify_password
from app.models.user import AuthProvider, User
from app.schemas.user import UserUpdate


async def get_user_by_id(db: AsyncSession, user_id: UUID) -> Optional[User]:
    """Fetch a user by their UUID."""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """Fetch a user by their email address."""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_google_id(db: AsyncSession, google_id: str) -> Optional[User]:
    """Fetch a user by their Google OAuth ID."""
    result = await db.execute(select(User).where(User.google_id == google_id))
    return result.scalar_one_or_none()


async def create_user(
    db: AsyncSession,
    email: str,
    password: Optional[str] = None,
    full_name: Optional[str] = None,
    avatar_url: Optional[str] = None,
    auth_provider: AuthProvider = AuthProvider.LOCAL,
    google_id: Optional[str] = None,
    is_verified: bool = False,
) -> User:
    """
    Create a new user account.

    For local auth, password is required.
    For Google OAuth, google_id is required and password is optional.

    Raises:
        ConflictError: If email already exists.
    """
    # Check for duplicate email
    existing = await get_user_by_email(db, email)
    if existing:
        raise ConflictError("An account with this email already exists")

    user = User(
        email=email,
        hashed_password=hash_password(password) if password else None,
        full_name=full_name,
        avatar_url=avatar_url,
        auth_provider=auth_provider,
        google_id=google_id,
        is_verified=is_verified,
    )
    db.add(user)
    await db.flush()  # Flush to get the ID without committing
    await db.refresh(user)
    return user


async def update_user_profile(
    db: AsyncSession,
    user: User,
    update_data: UserUpdate,
) -> User:
    """
    Update a user's profile fields.
    Only updates fields that are explicitly set (not None).
    """
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(user, field, value)
    await db.flush()
    await db.refresh(user)
    return user


async def change_user_password(
    db: AsyncSession,
    user: User,
    current_password: str,
    new_password: str,
) -> User:
    """
    Change a user's password.

    Verifies the current password before allowing the change.
    Only works for users with local auth (have a password set).

    Raises:
        AuthenticationError: If current password is incorrect.
        ConflictError: If user is OAuth-only (no password to change).
    """
    from app.core.exceptions import AuthenticationError

    if not user.hashed_password:
        raise ConflictError(
            "Cannot change password for OAuth-only accounts. "
            "Please set a password first."
        )

    if not verify_password(current_password, user.hashed_password):
        raise AuthenticationError("Current password is incorrect")

    user.hashed_password = hash_password(new_password)
    await db.flush()
    await db.refresh(user)
    return user


async def link_google_account(
    db: AsyncSession,
    user: User,
    google_id: str,
    avatar_url: Optional[str] = None,
) -> User:
    """Link a Google account to an existing user."""
    user.google_id = google_id
    if avatar_url and not user.avatar_url:
        user.avatar_url = avatar_url
    if user.auth_provider == AuthProvider.LOCAL:
        # Keep as local — they now have both auth methods
        pass
    await db.flush()
    await db.refresh(user)
    return user


async def soft_delete_user(db: AsyncSession, user: User) -> User:
    """Soft-delete a user by setting is_active to False."""
    user.is_active = False
    await db.flush()
    await db.refresh(user)
    return user
