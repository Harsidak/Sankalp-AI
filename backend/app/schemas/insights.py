"""
Pydantic schemas for the insights domain.

Insights are correlations rather than counts: how mood moves with a habit,
with the day of the week, with what the user wrote about. Every field here
is computed by a SQL aggregation in `services/insights_service.py` -- none
of it is stored.
"""

from typing import Optional

from pydantic import BaseModel, Field


class HabitMoodImpact(BaseModel):
    """
    Average mood on days a habit was kept versus days it was not.

    `delta` is the number the user actually cares about: the mood
    difference attributable to keeping the habit. It is null until both
    sides have at least one day, because a difference against nothing is
    not a difference.
    """

    habit_id: str
    name: str
    color: str
    days_done: int = Field(..., description="Check-in days on which the habit was completed")
    days_missed: int = Field(..., description="Check-in days on which it was not")
    mood_when_done: Optional[float] = None
    mood_when_missed: Optional[float] = None
    delta: Optional[float] = Field(
        None, description="mood_when_done - mood_when_missed, null if either side is empty"
    )


class WeekdayMood(BaseModel):
    """Average mood and energy for one day of the week."""

    weekday: int = Field(..., ge=0, le=6, description="0 = Monday ... 6 = Sunday")
    label: str
    avg_mood: Optional[float] = None
    avg_energy: Optional[float] = None
    checkins: int


class MoodBucket(BaseModel):
    """How many check-ins landed on a given 1-5 mood score."""

    score: int = Field(..., ge=1, le=5)
    count: int


class TagMood(BaseModel):
    """Average mood on the days a tag was used in the journal."""

    name: str
    color: str
    entries: int
    avg_mood: Optional[float] = None


class InsightsSummary(BaseModel):
    """Everything the insights page renders, in one payload."""

    range_days: int
    habit_impact: list[HabitMoodImpact] = []
    weekday: list[WeekdayMood] = []
    mood_distribution: list[MoodBucket] = []
    tag_mood: list[TagMood] = []
    best_weekday: Optional[str] = None
    hardest_weekday: Optional[str] = None
    headline: Optional[str] = Field(
        None,
        description="Plain-language reading of the strongest signal, or null if the data is too thin",
    )
