"""
User and RefreshToken ORM models.

User supports both local (email/password) and OAuth (Google) authentication.
RefreshToken stores hashed refresh tokens for secure token rotation.
"""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.core.types import GUID


class AuthProvider(str, enum.Enum):
    """Authentication provider for the user account."""
    LOCAL = "local"
    GOOGLE = "google"


class User(Base):
    """
    User account table.

    Supports both local (email/password) and Google OAuth authentication.
    hashed_password is nullable to support OAuth-only accounts.
    """

    __tablename__ = "users"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=True)  # Nullable for OAuth-only users
    full_name = Column(String(255), nullable=True)
    avatar_url = Column(Text, nullable=True)

    # Account status
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)

    # Auth provider tracking
    auth_provider = Column(
        Enum(AuthProvider, values_callable=lambda e: [m.value for m in e]),
        default=AuthProvider.LOCAL,
        nullable=False,
    )
    google_id = Column(String(255), unique=True, nullable=True, index=True)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    refresh_tokens = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    chat_sessions = relationship(
        "ChatSession",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    checkins = relationship(
        "CheckIn",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    journal_entries = relationship(
        "JournalEntry",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    tags = relationship(
        "Tag",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    habits = relationship(
        "Habit",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    def __repr__(self) -> str:
        return f"<User {self.email}>"


class RefreshToken(Base):
    """
    Stored refresh tokens for secure token rotation.

    We store a hash of the refresh token (not the token itself) so that
    even if the DB is compromised, tokens cannot be replayed.
    The is_revoked flag supports explicit logout and token rotation.
    """

    __tablename__ = "refresh_tokens"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    token_hash = Column(String(255), unique=True, nullable=False, index=True)
    user_id = Column(
        GUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    is_revoked = Column(Boolean, default=False, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user = relationship("User", back_populates="refresh_tokens")

    def __repr__(self) -> str:
        return f"<RefreshToken user_id={self.user_id} revoked={self.is_revoked}>"
