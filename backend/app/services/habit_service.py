"""
Habit service: habit CRUD, day logging, and streak computation.

Completion is modelled as the presence of a habit_logs row, so marking a
day done is an insert and undoing it is a delete. That keeps the toggle
idempotent and makes UNIQUE(habit_id, completed_date) the guard against
double-logging.
"""

from datetime import date, timedelta
from typing import Iterable, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError
from app.models.wellness import Habit, HabitLog
from app.schemas.wellness import HabitCreate, HabitUpdate


# --------------------------------------------------------------------------
# Streak maths (pure functions - no database, trivially testable)
# --------------------------------------------------------------------------

def compute_current_streak(completed: Iterable[date], today: Optional[date] = None) -> int:
    """
    Count consecutive completed days ending today or yesterday.

    Yesterday counts as the anchor so a streak is not reported as broken
    merely because the user has not checked in yet today.
    """
    today = today or date.today()
    days = set(completed)
    if not days:
        return 0

    if today in days:
        cursor = today
    elif (today - timedelta(days=1)) in days:
        cursor = today - timedelta(days=1)
    else:
        return 0

    streak = 0
    while cursor in days:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def compute_longest_streak(completed: Iterable[date]) -> int:
    """Length of the longest run of consecutive completed days, ever."""
    days = sorted(set(completed))
    if not days:
        return 0

    longest = 1
    run = 1
    for previous, current in zip(days, days[1:]):
        if (current - previous).days == 1:
            run += 1
            longest = max(longest, run)
        else:
            run = 1
    return longest


# --------------------------------------------------------------------------
# Queries
# --------------------------------------------------------------------------

async def get_owned(db: AsyncSession, user_id: UUID, habit_id: UUID) -> Habit:
    """
    Fetch a habit belonging to this user, with its logs loaded.

    Raises:
        NotFoundError: If it does not exist or belongs to someone else.
    """
    result = await db.execute(
        select(Habit)
        .where(Habit.id == habit_id, Habit.user_id == user_id)
        .options(selectinload(Habit.logs))
    )
    habit = result.scalar_one_or_none()
    if not habit:
        raise NotFoundError("Habit not found")
    return habit


async def list_habits(
    db: AsyncSession,
    user_id: UUID,
    include_archived: bool = False,
) -> list[Habit]:
    """List the user's habits, oldest first, with logs loaded."""
    query = (
        select(Habit)
        .where(Habit.user_id == user_id)
        .options(selectinload(Habit.logs))
        .order_by(Habit.created_at.asc())
    )
    if not include_archived:
        query = query.where(Habit.is_archived.is_(False))

    result = await db.execute(query)
    return list(result.scalars().unique().all())


def summarize(habit: Habit, today: Optional[date] = None) -> dict:
    """
    Build the derived fields the API exposes for a habit.

    Kept separate from the ORM model so streak logic stays testable
    without a database.
    """
    today = today or date.today()
    completed = [log.completed_date for log in habit.logs]
    return {
        "completed_dates": sorted(completed),
        "current_streak": compute_current_streak(completed, today),
        "longest_streak": compute_longest_streak(completed),
        "completed_today": today in set(completed),
    }


# --------------------------------------------------------------------------
# Mutations
# --------------------------------------------------------------------------

async def create(db: AsyncSession, user_id: UUID, data: HabitCreate) -> Habit:
    """Create a habit."""
    habit = Habit(
        user_id=user_id,
        name=data.name,
        icon=data.icon,
        color=data.color,
        target_per_week=data.target_per_week,
    )
    db.add(habit)
    await db.flush()
    await db.refresh(habit, attribute_names=["logs"])
    return habit


async def update(
    db: AsyncSession,
    user_id: UUID,
    habit_id: UUID,
    data: HabitUpdate,
) -> Habit:
    """Patch a habit's name, icon, colour, target, or archived flag."""
    habit = await get_owned(db, user_id, habit_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(habit, field, value)

    await db.flush()
    await db.refresh(habit, attribute_names=["logs"])
    return habit


async def delete(db: AsyncSession, user_id: UUID, habit_id: UUID) -> None:
    """
    Permanently delete a habit and its logs (ON DELETE CASCADE).

    Prefer archiving via update() when the history should be kept.
    """
    habit = await get_owned(db, user_id, habit_id)
    await db.delete(habit)
    await db.flush()


async def toggle_log(
    db: AsyncSession,
    user_id: UUID,
    habit_id: UUID,
    on: Optional[date] = None,
) -> tuple[Habit, date, bool]:
    """
    Flip a habit's completion for one day: insert if absent, delete if present.

    Returns:
        (habit with logs refreshed, the day toggled, whether it is now complete)
    """
    habit = await get_owned(db, user_id, habit_id)
    day = on or date.today()

    result = await db.execute(
        select(HabitLog).where(
            HabitLog.habit_id == habit.id,
            HabitLog.completed_date == day,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        await db.delete(existing)
        now_complete = False
    else:
        db.add(HabitLog(habit_id=habit.id, completed_date=day))
        now_complete = True

    await db.flush()
    await db.refresh(habit, attribute_names=["logs"])
    return habit, day, now_complete
