"""
Insights service: the correlation queries.

Where `dashboard_service` counts things, this module relates them -- mood
against habits, against weekdays, against what the user wrote about. These
are the queries worth reading in this project: conditional aggregation
(AVG over a CASE), a deliberate cross join, and a LEFT OUTER JOIN whose
null side carries the meaning.

None of it is computed in Python. The one place the dialect leaks through
is the weekday extraction, which MySQL and SQLite spell differently; see
`_weekday_expr`.
"""

from datetime import date, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import Integer, case, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.models.wellness import (
    CheckIn,
    EntryTag,
    Habit,
    HabitLog,
    JournalEntry,
    Tag,
)
from app.schemas.insights import (
    HabitMoodImpact,
    InsightsSummary,
    MoodBucket,
    TagMood,
    WeekdayMood,
)

WEEKDAY_LABELS = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]

# A correlation drawn from a handful of days is noise. Below this many
# observations on either side we still report the numbers, but refuse to
# headline them.
MIN_DAYS_FOR_SIGNAL = 4


def _round(value, digits: int = 2) -> Optional[float]:
    """Round a SQL aggregate to a float, preserving None for empty groups."""
    return round(float(value), digits) if value is not None else None


def _dialect_name(db: AsyncSession) -> str:
    """
    The dialect behind this session, defaulting to sqlite.

    The tests run these same queries against SQLite while production is
    MySQL, and weekday extraction is the one thing the two do not share.
    """
    try:
        return db.get_bind().dialect.name
    except Exception:  # pragma: no cover - only if the session has no bind
        return "sqlite"


def _weekday_expr(dialect: str):
    """
    An expression yielding 0 = Monday .. 6 = Sunday, computed in the database.

    MySQL's DAYOFWEEK() is 1 = Sunday .. 7 = Saturday; SQLite's
    strftime('%w') is 0 = Sunday .. 6 = Saturday and returns text. Both are
    rotated onto an ISO-style Monday-first week, so the frontend never has
    to know which database answered.
    """
    if dialect == "mysql":
        return (func.dayofweek(CheckIn.checkin_date) + 5) % 7
    return (cast(func.strftime("%w", CheckIn.checkin_date), Integer) + 6) % 7


# --------------------------------------------------------------------------
# Queries
# --------------------------------------------------------------------------

async def habit_mood_impact(
    db: AsyncSession,
    user_id: UUID,
    start: date,
    end: date,
) -> list[HabitMoodImpact]:
    """
    Average mood on days each habit was kept, versus days it was not.

    The shape of this query is the point:

        habits CROSS JOIN checkins   -- every (habit, checked-in day) pair
          LEFT JOIN habit_logs       -- did that habit happen on that day?

    The cross join builds the full grid of days each habit could have been
    kept, and the left join's null side is exactly the days it was not. One
    pass of conditional aggregation then splits the mood average in two.

    A habit is only measured from the point it started being tracked, so one
    added yesterday is not reported as having been missed all month. That
    point is the earlier of the habit row's creation date and its first log,
    because a log may predate the row -- back-filled history and seeded demo
    data both do exactly that, and keying off created_at alone would throw
    the entire history away.
    """
    done = HabitLog.id.isnot(None)
    missed = HabitLog.id.is_(None)

    # The subquery needs its own alias of habit_logs: the table is already in
    # the enclosing FROM via the outer join, and without an alias SQLAlchemy
    # correlates against *that* row instead of scanning the habit's full log.
    earliest_log = aliased(HabitLog)
    first_log = (
        select(func.min(earliest_log.completed_date))
        .where(earliest_log.habit_id == Habit.id)
        .correlate(Habit)
        .scalar_subquery()
    )

    # LEAST() is MySQL-only and SQLite spells it MIN(); a CASE is portable.
    created_day = func.date(Habit.created_at)
    tracked_from = case((first_log < created_day, first_log), else_=created_day)

    stmt = (
        select(
            Habit.id,
            Habit.name,
            Habit.color,
            func.count(case((done, 1))).label("days_done"),
            func.count(case((missed, 1))).label("days_missed"),
            func.avg(case((done, CheckIn.mood_score))).label("mood_done"),
            func.avg(case((missed, CheckIn.mood_score))).label("mood_missed"),
        )
        .select_from(Habit)
        .join(CheckIn, CheckIn.user_id == Habit.user_id)
        .outerjoin(
            HabitLog,
            (HabitLog.habit_id == Habit.id)
            & (HabitLog.completed_date == CheckIn.checkin_date),
        )
        .where(
            Habit.user_id == user_id,
            Habit.is_archived.is_(False),
            CheckIn.checkin_date >= start,
            CheckIn.checkin_date <= end,
            CheckIn.checkin_date >= tracked_from,
        )
        .group_by(Habit.id, Habit.name, Habit.color)
        .order_by(Habit.name.asc())
    )

    rows = (await db.execute(stmt)).all()

    impacts: list[HabitMoodImpact] = []
    for row in rows:
        mood_done = _round(row.mood_done)
        mood_missed = _round(row.mood_missed)
        impacts.append(
            HabitMoodImpact(
                habit_id=str(row.id),
                name=row.name,
                color=row.color,
                days_done=int(row.days_done or 0),
                days_missed=int(row.days_missed or 0),
                mood_when_done=mood_done,
                mood_when_missed=mood_missed,
                delta=(
                    round(mood_done - mood_missed, 2)
                    if mood_done is not None and mood_missed is not None
                    else None
                ),
            )
        )

    # Strongest effect first: that is the one the page leads with. Habits
    # with no measurable delta sort last rather than being dropped.
    impacts.sort(key=lambda i: (i.delta is None, -(i.delta or 0)))
    return impacts


async def weekday_mood(
    db: AsyncSession,
    user_id: UUID,
    start: date,
    end: date,
) -> list[WeekdayMood]:
    """
    Average mood and energy grouped by day of the week.

    Every weekday comes back, including ones with no check-ins, so the
    chart keeps seven columns and does not silently re-scale.
    """
    weekday = _weekday_expr(_dialect_name(db)).label("weekday")

    stmt = (
        select(
            weekday,
            func.avg(CheckIn.mood_score).label("avg_mood"),
            func.avg(CheckIn.energy_score).label("avg_energy"),
            func.count(CheckIn.id).label("checkins"),
        )
        .where(
            CheckIn.user_id == user_id,
            CheckIn.checkin_date >= start,
            CheckIn.checkin_date <= end,
        )
        .group_by(weekday)
    )

    by_day = {int(row.weekday): row for row in (await db.execute(stmt)).all()}

    return [
        WeekdayMood(
            weekday=index,
            label=label,
            avg_mood=_round(by_day[index].avg_mood) if index in by_day else None,
            avg_energy=_round(by_day[index].avg_energy) if index in by_day else None,
            checkins=int(by_day[index].checkins) if index in by_day else 0,
        )
        for index, label in enumerate(WEEKDAY_LABELS)
    ]


async def mood_distribution(
    db: AsyncSession,
    user_id: UUID,
    start: date,
    end: date,
) -> list[MoodBucket]:
    """How many check-ins landed on each 1-5 mood score, zeros included."""
    stmt = (
        select(CheckIn.mood_score, func.count(CheckIn.id).label("count"))
        .where(
            CheckIn.user_id == user_id,
            CheckIn.checkin_date >= start,
            CheckIn.checkin_date <= end,
        )
        .group_by(CheckIn.mood_score)
    )
    counts = {
        int(row.mood_score): int(row.count) for row in (await db.execute(stmt)).all()
    }
    return [MoodBucket(score=score, count=counts.get(score, 0)) for score in range(1, 6)]


async def tag_mood(
    db: AsyncSession,
    user_id: UUID,
    start: date,
    end: date,
    limit: int = 8,
) -> list[TagMood]:
    """
    Average mood on the days each tag was written about.

    Four tables deep: tags -> entry_tags -> journal_entries, then a LEFT
    JOIN onto that day's check-in. It is a left join because an entry
    written on a day with no check-in should still count toward the tag's
    entry total; it simply contributes nothing to the mood average.

    COUNT(DISTINCT journal_entries.id) rather than COUNT(*): the join to
    checkins cannot fan out today, but a plain count here would quietly
    become wrong the day it can.
    """
    entry_day = func.date(JournalEntry.created_at)

    stmt = (
        select(
            Tag.name,
            Tag.color,
            func.count(func.distinct(JournalEntry.id)).label("entries"),
            func.avg(CheckIn.mood_score).label("avg_mood"),
        )
        .select_from(Tag)
        .join(EntryTag, EntryTag.tag_id == Tag.id)
        .join(JournalEntry, JournalEntry.id == EntryTag.entry_id)
        .outerjoin(
            CheckIn,
            (CheckIn.user_id == Tag.user_id) & (CheckIn.checkin_date == entry_day),
        )
        .where(
            Tag.user_id == user_id,
            entry_day >= start,
            entry_day <= end,
        )
        .group_by(Tag.id, Tag.name, Tag.color)
        .order_by(func.count(func.distinct(JournalEntry.id)).desc(), Tag.name.asc())
        .limit(limit)
    )

    return [
        TagMood(
            name=row.name,
            color=row.color,
            entries=int(row.entries or 0),
            avg_mood=_round(row.avg_mood),
        )
        for row in (await db.execute(stmt)).all()
    ]


# --------------------------------------------------------------------------
# Assembly
# --------------------------------------------------------------------------

def _headline(
    impacts: list[HabitMoodImpact],
    weekdays: list[WeekdayMood],
) -> Optional[str]:
    """
    Turn the strongest signal into one sentence.

    Deliberately not an AI call: the numbers already say this, and a
    sentence derived straight from them cannot hallucinate. Returns None
    when nothing clears the noise floor, and the page then says so.
    """
    strong = [
        i
        for i in impacts
        if i.delta is not None
        and i.days_done >= MIN_DAYS_FOR_SIGNAL
        and i.days_missed >= MIN_DAYS_FOR_SIGNAL
    ]
    if strong:
        best = max(strong, key=lambda i: abs(i.delta))
        if abs(best.delta) >= 0.3:
            direction = "higher" if best.delta > 0 else "lower"
            return (
                f"Your mood runs {abs(best.delta):.1f} points {direction} "
                f"on days you keep “{best.name}”."
            )

    rated = [w for w in weekdays if w.avg_mood is not None and w.checkins >= 2]
    if len(rated) >= 3:
        best = max(rated, key=lambda w: w.avg_mood)
        worst = min(rated, key=lambda w: w.avg_mood)
        if best.avg_mood - worst.avg_mood >= 0.4:
            return f"{best.label}s read best for you; {worst.label}s are the hardest."

    return None


async def build_summary(
    db: AsyncSession,
    user_id: UUID,
    days: int = 30,
) -> InsightsSummary:
    """Assemble the whole insights payload for the last N days."""
    end = date.today()
    start = end - timedelta(days=days - 1)

    impacts = await habit_mood_impact(db, user_id, start, end)
    weekdays = await weekday_mood(db, user_id, start, end)
    distribution = await mood_distribution(db, user_id, start, end)
    tags = await tag_mood(db, user_id, start, end)

    rated = [w for w in weekdays if w.avg_mood is not None and w.checkins >= 2]

    return InsightsSummary(
        range_days=days,
        habit_impact=impacts,
        weekday=weekdays,
        mood_distribution=distribution,
        tag_mood=tags,
        best_weekday=max(rated, key=lambda w: w.avg_mood).label if rated else None,
        hardest_weekday=min(rated, key=lambda w: w.avg_mood).label if rated else None,
        headline=_headline(impacts, weekdays),
    )
