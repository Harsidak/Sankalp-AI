"""
Pydantic schemas for the wellness domain.

Request schemas carry the validation the database cannot express
conveniently (score ranges, hex colour format); response schemas define
exactly what the frontend receives.
"""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

HEX_COLOR = r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$"


# --------------------------------------------------------------------------
# Check-ins
# --------------------------------------------------------------------------

class CheckInCreate(BaseModel):
    """Create or replace today's check-in."""

    mood_score: int = Field(..., ge=1, le=5, description="Mood, 1 (low) to 5 (high)")
    energy_score: int = Field(..., ge=1, le=5, description="Energy, 1 (low) to 5 (high)")
    note: Optional[str] = Field(None, max_length=2000)
    checkin_date: Optional[date] = Field(
        None,
        description="Defaults to today. Cannot be in the future.",
    )

    @field_validator("checkin_date")
    @classmethod
    def not_in_future(cls, v: Optional[date]) -> Optional[date]:
        if v and v > date.today():
            raise ValueError("checkin_date cannot be in the future")
        return v


class CheckInUpdate(BaseModel):
    """Partial update of an existing check-in."""

    mood_score: Optional[int] = Field(None, ge=1, le=5)
    energy_score: Optional[int] = Field(None, ge=1, le=5)
    note: Optional[str] = Field(None, max_length=2000)


class CheckInRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    mood_score: int
    energy_score: int
    note: Optional[str] = None
    checkin_date: date
    created_at: datetime


# --------------------------------------------------------------------------
# Tags
# --------------------------------------------------------------------------

class TagCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    color: str = Field("#6366f1", pattern=HEX_COLOR)

    @field_validator("name")
    @classmethod
    def normalize(cls, v: str) -> str:
        return v.strip().lower()


class TagUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    color: Optional[str] = Field(None, pattern=HEX_COLOR)

    @field_validator("name")
    @classmethod
    def normalize(cls, v: Optional[str]) -> Optional[str]:
        return v.strip().lower() if v else v


class TagRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    color: str


class TagWithCount(TagRead):
    """A tag plus how many journal entries currently carry it."""

    entry_count: int = 0


# --------------------------------------------------------------------------
# Journal
# --------------------------------------------------------------------------

class JournalCreate(BaseModel):
    title: str = Field("Untitled", max_length=255)
    content: str = Field(..., min_length=1)
    tag_ids: list[str] = Field(default_factory=list)


class JournalUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    content: Optional[str] = Field(None, min_length=1)
    tag_ids: Optional[list[str]] = Field(
        None,
        description="When present, replaces the entry's whole tag set.",
    )


class JournalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    content: str
    tags: list[TagRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


# --------------------------------------------------------------------------
# Habits
# --------------------------------------------------------------------------

class HabitCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    icon: Optional[str] = Field(None, max_length=50)
    color: str = Field("#10b981", pattern=HEX_COLOR)
    target_per_week: int = Field(7, ge=1, le=7)


class HabitUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    icon: Optional[str] = Field(None, max_length=50)
    color: Optional[str] = Field(None, pattern=HEX_COLOR)
    target_per_week: Optional[int] = Field(None, ge=1, le=7)
    is_archived: Optional[bool] = None


class HabitRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    icon: Optional[str] = None
    color: str
    target_per_week: int
    is_archived: bool
    created_at: datetime

    # Derived fields, computed by the service rather than stored.
    completed_dates: list[date] = Field(default_factory=list)
    current_streak: int = 0
    longest_streak: int = 0
    completed_today: bool = False


class HabitLogToggle(BaseModel):
    """Mark a habit done (or undone) on a given day. Defaults to today."""

    completed_date: Optional[date] = None

    @field_validator("completed_date")
    @classmethod
    def not_in_future(cls, v: Optional[date]) -> Optional[date]:
        if v and v > date.today():
            raise ValueError("completed_date cannot be in the future")
        return v


class HabitLogResult(BaseModel):
    habit_id: str
    completed_date: date
    completed: bool
    current_streak: int
    longest_streak: int


# --------------------------------------------------------------------------
# Dashboard
# --------------------------------------------------------------------------

class MoodPoint(BaseModel):
    """One day on the mood trend line."""

    day: date
    mood: Optional[float] = None
    energy: Optional[float] = None


class TagFrequency(BaseModel):
    name: str
    color: str
    count: int


class HabitCompletion(BaseModel):
    habit_id: str
    name: str
    color: str
    completions: int
    target: int
    current_streak: int


class DashboardSummary(BaseModel):
    """Everything the dashboard needs, in one round trip."""

    range_days: int
    mood_trend: list[MoodPoint] = Field(default_factory=list)
    average_mood: Optional[float] = None
    average_energy: Optional[float] = None
    checkin_count: int = 0
    journal_count: int = 0
    top_tags: list[TagFrequency] = Field(default_factory=list)
    habit_completions: list[HabitCompletion] = Field(default_factory=list)
    longest_active_streak: int = 0
