"""
ChatSession and ChatMessage ORM models.

Persists AI chat conversations so users can revisit past sessions.
Each session belongs to a user and contains an ordered sequence of messages.
"""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.core.types import GUID


class MessageRole(str, enum.Enum):
    """Role of a chat message sender."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatSession(Base):
    """
    A conversation session between a user and the AI.
    Contains metadata about the session (title, model used).
    """

    __tablename__ = "chat_sessions"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        GUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = Column(String(255), default="New Chat", nullable=False)
    model_name = Column(String(100), nullable=True)  # Which LLM model was used

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
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship(
        "ChatMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ChatMessage.sequence_number",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<ChatSession {self.title}>"


class ChatMessage(Base):
    """
    Individual message in a chat session.
    Ordered by sequence_number within a session.
    """

    __tablename__ = "chat_messages"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        GUID(),
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role = Column(
        Enum(MessageRole, values_callable=lambda e: [m.value for m in e]),
        nullable=False,
    )
    content = Column(Text, nullable=False)
    sequence_number = Column(Integer, nullable=False)  # Order within session

    # Token usage tracking (useful for billing/analytics)
    token_count = Column(Integer, nullable=True)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    session = relationship("ChatSession", back_populates="messages")

    def __repr__(self) -> str:
        return f"<ChatMessage {self.role.value} #{self.sequence_number}>"
