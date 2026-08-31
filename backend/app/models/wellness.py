"""
Wellness domain ORM models: daily check-ins, journal entries, tags, habits.

Schema notes (the deliberate DBMS design decisions):

- Check-ins and journal entries are separate tables rather than one
  polymorphic "entries" table. They differ in cardinality (at most one
  check-in per day vs. many journal entries per day) and in columns;
  merging them would force nullable columns plus a discriminator, which
  is strictly worse normalization.
- Uniqueness is enforced by database constraints, not application code:
  one check-in per user per day, one habit log per habit per day, and
  tag names unique per user.
- journal_entries <-> tags is a true many-to-many resolved by the
  entry_tags join table, whose primary key is the composite of both
  foreign keys.
- Every table descends from users via ON DELETE CASCADE, so deleting an
  account removes all of its data in a single statement.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.core.types import GUID

# Shared MySQL table options - InnoDB is required for foreign keys,
# utf8mb4 is required for emoji and non-Latin journal text.
_MYSQL_OPTS = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}


class CheckIn(Base):
    """
    One mood/energy check-in per user per calendar day.

    The UNIQUE(user_id, checkin_date) constraint is what makes "daily"
    an actual guarantee rather than a convention the API tries to honour.
    """

    __tablename__ = "checkins"
    __table_args__ = (
        # UNIQUE already creates a (user_id, checkin_date) B-tree, which
        # the dashboard's range scans use; a separate index would duplicate it.
        UniqueConstraint("user_id", "checkin_date", name="uq_checkins_user_date"),
        _MYSQL_OPTS,
    )

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        GUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    mood_score = Column(SmallInteger, nullable=False)  # 1..5, range checked in schema
    energy_score = Column(SmallInteger, nullable=False)  # 1..5
    note = Column(Text, nullable=True)
    checkin_date = Column(Date, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user = relationship("User", back_populates="checkins")

    def __repr__(self) -> str:
        return f"<CheckIn {self.checkin_date} mood={self.mood_score}>"


class JournalEntry(Base):
    """
    A free-text journal entry. Many per user, many per day.

    The FULLTEXT index backs server-side search over title and content;
    it requires InnoDB (MySQL 5.6+), which _MYSQL_OPTS pins.
    """

    __tablename__ = "journal_entries"
    __table_args__ = (
        Index("ix_journal_user_created", "user_id", "created_at"),
        Index("ft_journal_search", "title", "content", mysql_prefix="FULLTEXT"),
        _MYSQL_OPTS,
    )

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        GUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    title = Column(String(255), nullable=False, default="Untitled")
    content = Column(Text, nullable=False)

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

    user = relationship("User", back_populates="journal_entries")
    tags = relationship(
        "Tag",
        secondary="entry_tags",
        back_populates="entries",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<JournalEntry {self.title!r}>"


class Tag(Base):
    """
    A user-defined label applied to journal entries.

    Tags are scoped per user - two users may both own a tag named "work"
    without collision, which UNIQUE(user_id, name) expresses exactly.
    """

    __tablename__ = "tags"
    __table_args__ = (
        # user_id leads this index, so lookups of "this user's tags" use it
        # too; a separate index on user_id alone would be redundant.
        UniqueConstraint("user_id", "name", name="uq_tags_user_name"),
        _MYSQL_OPTS,
    )

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        GUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    name = Column(String(50), nullable=False)
    color = Column(String(7), nullable=False, default="#6366f1")  # hex, e.g. #6366f1

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user = relationship("User", back_populates="tags")
    entries = relationship(
        "JournalEntry",
        secondary="entry_tags",
        back_populates="tags",
    )

    def __repr__(self) -> str:
        return f"<Tag {self.name}>"


class EntryTag(Base):
    """
    Join table resolving the journal_entries <-> tags many-to-many.

    It carries no surrogate key: the composite (entry_id, tag_id) is the
    primary key, which both identifies the row and prevents duplicates.
    """

    __tablename__ = "entry_tags"
    __table_args__ = (_MYSQL_OPTS,)

    entry_id = Column(
        GUID(),
        ForeignKey("journal_entries.id", ondelete="CASCADE"),
        primary_key=True,
    )
    tag_id = Column(
        GUID(),
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
    )

    def __repr__(self) -> str:
        return f"<EntryTag {self.entry_id}:{self.tag_id}>"


class Habit(Base):
    """
    A repeating behaviour the user wants to track (e.g. "Walk 20 minutes").

    Habits are archived rather than deleted so their historical logs stay
    intact and streak history remains truthful.
    """

    __tablename__ = "habits"
    __table_args__ = (
        Index("ix_habits_user_archived", "user_id", "is_archived"),
        _MYSQL_OPTS,
    )

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        GUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    name = Column(String(100), nullable=False)
    icon = Column(String(50), nullable=True)  # icon sprite id, e.g. "moon"
    color = Column(String(7), nullable=False, default="#10b981")
    target_per_week = Column(SmallInteger, nullable=False, default=7)
    is_archived = Column(Boolean, nullable=False, default=False)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user = relationship("User", back_populates="habits")
    logs = relationship(
        "HabitLog",
        back_populates="habit",
        cascade="all, delete-orphan",
        order_by="HabitLog.completed_date",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Habit {self.name}>"


class HabitLog(Base):
    """
    A single day on which a habit was completed.

    Completion is modelled as the presence of a row, so "mark done" is an
    insert and "undo" is a delete. UNIQUE(habit_id, completed_date) makes
    double-logging impossible at the database level.
    """

    __tablename__ = "habit_logs"
    __table_args__ = (
        # As above: the UNIQUE constraint is the index range scans use.
        UniqueConstraint("habit_id", "completed_date", name="uq_habit_logs_habit_date"),
        _MYSQL_OPTS,
    )

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    habit_id = Column(
        GUID(),
        ForeignKey("habits.id", ondelete="CASCADE"),
        nullable=False,
    )
    completed_date = Column(Date, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    habit = relationship("Habit", back_populates="logs")

    def __repr__(self) -> str:
        return f"<HabitLog {self.completed_date}>"
