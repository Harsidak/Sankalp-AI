"""
Dashboard service: the aggregate queries behind the analytics screen.

These are deliberately written as real SQL aggregations (GROUP BY, COUNT,
AVG, LEFT OUTER JOIN across four tables) rather than by loading rows and
summing them in Python. The database is the right place for this work,
and the queries are the part of the schema design worth showing.
"""

from datetime import date, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.wellness import (
    CheckIn,
    EntryTag,
    Habit,
    HabitLog,
    JournalEntry,
    Tag,
)
from app.services import habit_service
from app.schemas.wellness import (
    DashboardSummary,
    HabitCompletion,
    MoodPoint,
    TagFrequency,
)


async def mood_trend(
    db: AsyncSession,
    user_id: UUID,
    start: date,
    end: date,
) -> list[MoodPoint]:
    """
    Mood and energy per day across the range, with gaps filled.

    Days without a check-in come back with null scores rather than being
    omitted, so the frontend can draw a broken line instead of silently
    connecting across a missing week.
    """
    result = await db.execute(
        select(CheckIn.checkin_date, CheckIn.mood_score, CheckIn.energy_score)
        .where(
            CheckIn.user_id == user_id,
            CheckIn.checkin_date >= start,
            CheckIn.checkin_date <= end,
        )
        .order_by(CheckIn.checkin_date.asc())
    )
    by_day = {row.checkin_date: row for row in result.all()}

    points: list[MoodPoint] = []
    cursor = start
    while cursor <= end:
        row = by_day.get(cursor)
        points.append(
            MoodPoint(
                day=cursor,
                mood=float(row.mood_score) if row else None,
                energy=float(row.energy_score) if row else None,
            )
        )
        cursor += timedelta(days=1)
    return points


async def mood_averages(
    db: AsyncSession,
    user_id: UUID,
    start: date,
    end: date,
) -> tuple[float | None, float | None, int]:
    """
    Average mood, average energy, and check-in count over the range.

    Returns:
        (average mood, average energy, number of check-ins)
    """
    result = await db.execute(
        select(
            func.avg(CheckIn.mood_score),
            func.avg(CheckIn.energy_score),
            func.count(CheckIn.id),
        ).where(
            CheckIn.user_id == user_id,
            CheckIn.checkin_date >= start,
            CheckIn.checkin_date <= end,
        )
    )
    avg_mood, avg_energy, count = result.one()
    return (
        round(float(avg_mood), 2) if avg_mood is not None else None,
        round(float(avg_energy), 2) if avg_energy is not None else None,
        int(count or 0),
    )


async def top_tags(
    db: AsyncSession,
    user_id: UUID,
    start: date,
    end: date,
    limit: int = 8,
) -> list[TagFrequency]:
    """
    The user's most-used tags in the range.

    Joins tags -> entry_tags -> journal_entries so the date filter applies
    to the entry, not the tag, then counts per tag.
    """
    stmt = (
        select(Tag.name, Tag.color, func.count(EntryTag.entry_id).label("count"))
        .join(EntryTag, EntryTag.tag_id == Tag.id)
        .join(JournalEntry, JournalEntry.id == EntryTag.entry_id)
        .where(
            Tag.user_id == user_id,
            func.date(JournalEntry.created_at) >= start,
            func.date(JournalEntry.created_at) <= end,
        )
        .group_by(Tag.id, Tag.name, Tag.color)
        .order_by(func.count(EntryTag.entry_id).desc(), Tag.name.asc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return [
        TagFrequency(name=row.name, color=row.color, count=int(row.count))
        for row in result.all()
    ]


async def journal_count(
    db: AsyncSession,
    user_id: UUID,
    start: date,
    end: date,
) -> int:
    """How many journal entries the user wrote in the range."""
    result = await db.execute(
        select(func.count(JournalEntry.id)).where(
            JournalEntry.user_id == user_id,
            func.date(JournalEntry.created_at) >= start,
            func.date(JournalEntry.created_at) <= end,
        )
    )
    return int(result.scalar_one() or 0)


async def habit_completions(
    db: AsyncSession,
    user_id: UUID,
    start: date,
    end: date,
) -> list[HabitCompletion]:
    """
    Completion counts per active habit over the range.

    The LEFT OUTER JOIN is what keeps a habit with zero completions in the
    result -- an inner join would hide exactly the habits the user most
    needs to see.
    """
    stmt = (
        select(
            Habit.id,
            Habit.name,
            Habit.color,
            Habit.target_per_week,
            func.count(HabitLog.id).label("completions"),
        )
        .outerjoin(
            HabitLog,
            (HabitLog.habit_id == Habit.id)
            & (HabitLog.completed_date >= start)
            & (HabitLog.completed_date <= end),
        )
        .where(Habit.user_id == user_id, Habit.is_archived.is_(False))
        .group_by(Habit.id, Habit.name, Habit.color, Habit.target_per_week)
        .order_by(func.count(HabitLog.id).desc(), Habit.name.asc())
    )
    result = await db.execute(stmt)
    rows = result.all()

    # Streaks span a habit's whole history, so they are computed from the
    # full log set rather than from the windowed counts above.
    habits = {h.id: h for h in await habit_service.list_habits(db, user_id)}

    completions: list[HabitCompletion] = []
    for row in rows:
        habit = habits.get(row.id)
        streak = (
            habit_service.compute_current_streak(
                [log.completed_date for log in habit.logs]
            )
            if habit
            else 0
        )
        completions.append(
            HabitCompletion(
                habit_id=str(row.id),
                name=row.name,
                color=row.color,
                completions=int(row.completions or 0),
                target=int(row.target_per_week),
                current_streak=streak,
            )
        )
    return completions


async def build_summary(
    db: AsyncSession,
    user_id: UUID,
    days: int = 30,
) -> DashboardSummary:
    """Assemble the whole dashboard payload for the last N days."""
    end = date.today()
    start = end - timedelta(days=days - 1)

    trend = await mood_trend(db, user_id, start, end)
    avg_mood, avg_energy, checkins = await mood_averages(db, user_id, start, end)
    tags = await top_tags(db, user_id, start, end)
    entries = await journal_count(db, user_id, start, end)
    habits = await habit_completions(db, user_id, start, end)

    return DashboardSummary(
        range_days=days,
        mood_trend=trend,
        average_mood=avg_mood,
        average_energy=avg_energy,
        checkin_count=checkins,
        journal_count=entries,
        top_tags=tags,
        habit_completions=habits,
        longest_active_streak=max(
            (h.current_streak for h in habits),
            default=0,
        ),
    )
