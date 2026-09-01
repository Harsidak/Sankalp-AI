"""
Tests for the insights correlation queries.

These run against SQLite while production is MySQL, which is the point of
several of them: the weekday rotation and the "earliest tracked day" CASE
are written to mean the same thing on both, and a test that only ever saw
one dialect would not catch a divergence.

The data in each test is constructed so the expected average is exact,
so an assertion failure points at the query rather than at rounding.
"""

from datetime import date, datetime, timedelta, timezone

import pytest

from app.models.user import AuthProvider, User
from app.models.wellness import CheckIn, Habit, HabitLog, JournalEntry, Tag
from app.services import insights_service

TODAY = date.today()


@pytest.fixture
async def user(db_session) -> User:
    """A saved user to hang insight data off."""
    u = User(
        email="insights@test.dev",
        hashed_password="not-a-real-hash",
        auth_provider=AuthProvider.LOCAL,
    )
    db_session.add(u)
    await db_session.flush()
    return u


async def _checkin(db, user, day: date, mood: int, energy: int = 3) -> CheckIn:
    row = CheckIn(
        user_id=user.id, checkin_date=day, mood_score=mood, energy_score=energy
    )
    db.add(row)
    await db.flush()
    return row


async def _habit(db, user, name: str, created: date | None = None) -> Habit:
    row = Habit(
        user_id=user.id,
        name=name,
        color="#10b981",
        target_per_week=7,
        created_at=datetime.combine(
            created or TODAY, datetime.min.time(), tzinfo=timezone.utc
        ),
    )
    db.add(row)
    await db.flush()
    return row


# --------------------------------------------------------------------------
# Habit / mood correlation
# --------------------------------------------------------------------------

async def test_habit_impact_splits_mood_by_whether_the_habit_was_kept(db_session, user):
    """
    Four check-in days: the habit is kept on the two good ones and missed
    on the two bad ones, so the delta is exactly 2.0.
    """
    start = TODAY - timedelta(days=3)
    habit = await _habit(db_session, user, "Walk", created=start)

    for offset, mood in enumerate([5, 5, 3, 3]):
        day = start + timedelta(days=offset)
        await _checkin(db_session, user, day, mood)
        if mood == 5:
            db_session.add(HabitLog(habit_id=habit.id, completed_date=day))
    await db_session.flush()

    impacts = await insights_service.habit_mood_impact(db_session, user.id, start, TODAY)

    assert len(impacts) == 1
    impact = impacts[0]
    assert impact.days_done == 2
    assert impact.days_missed == 2
    assert impact.mood_when_done == 5.0
    assert impact.mood_when_missed == 3.0
    assert impact.delta == 2.0


async def test_habit_impact_counts_only_days_with_a_checkin(db_session, user):
    """
    The cross join is against check-ins, not against the calendar. A day the
    user never rated contributes to neither side of the average.
    """
    start = TODAY - timedelta(days=3)
    habit = await _habit(db_session, user, "Read", created=start)

    # Logged on all four days, but only two of them were ever checked in.
    for offset in range(4):
        db_session.add(
            HabitLog(habit_id=habit.id, completed_date=start + timedelta(days=offset))
        )
    await _checkin(db_session, user, start, 4)
    await _checkin(db_session, user, start + timedelta(days=1), 4)
    await db_session.flush()

    impact = (
        await insights_service.habit_mood_impact(db_session, user.id, start, TODAY)
    )[0]

    assert impact.days_done == 2
    assert impact.days_missed == 0
    assert impact.mood_when_done == 4.0
    # One-sided evidence is not a correlation.
    assert impact.delta is None


async def test_habit_impact_ignores_days_before_tracking_began(db_session, user):
    """
    A habit added today must not be reported as missed for the whole window.
    """
    start = TODAY - timedelta(days=4)
    for offset in range(5):
        await _checkin(db_session, user, start + timedelta(days=offset), 3)

    habit = await _habit(db_session, user, "Meditate", created=TODAY)
    db_session.add(HabitLog(habit_id=habit.id, completed_date=TODAY))
    await db_session.flush()

    impact = (
        await insights_service.habit_mood_impact(db_session, user.id, start, TODAY)
    )[0]

    assert impact.days_done == 1
    assert impact.days_missed == 0


async def test_habit_impact_measures_from_first_log_when_it_predates_creation(
    db_session, user
):
    """
    Back-filled history counts. The habit row is created today, but its logs
    reach back four days, so tracking is measured from the first log.
    """
    start = TODAY - timedelta(days=4)
    for offset in range(5):
        await _checkin(db_session, user, start + timedelta(days=offset), 3)

    habit = await _habit(db_session, user, "Backfilled", created=TODAY)
    for offset in (0, 1):
        db_session.add(
            HabitLog(habit_id=habit.id, completed_date=start + timedelta(days=offset))
        )
    await db_session.flush()

    impact = (
        await insights_service.habit_mood_impact(db_session, user.id, start, TODAY)
    )[0]

    assert impact.days_done == 2
    assert impact.days_missed == 3  # the remaining checked-in days in the window


async def test_habit_impact_excludes_archived_habits(db_session, user):
    start = TODAY - timedelta(days=2)
    habit = await _habit(db_session, user, "Retired", created=start)
    habit.is_archived = True
    await _checkin(db_session, user, start, 3)
    await db_session.flush()

    assert await insights_service.habit_mood_impact(
        db_session, user.id, start, TODAY
    ) == []


async def test_habit_impact_does_not_leak_across_users(db_session, user):
    """
    The cross join is joined on user_id; another account's check-ins must
    not widen this user's grid.
    """
    start = TODAY - timedelta(days=1)
    other = User(
        email="stranger@test.dev",
        hashed_password="x",
        auth_provider=AuthProvider.LOCAL,
    )
    db_session.add(other)
    await db_session.flush()

    await _checkin(db_session, other, start, 1)
    await _checkin(db_session, other, TODAY, 1)

    habit = await _habit(db_session, user, "Mine", created=start)
    await _checkin(db_session, user, TODAY, 5)
    db_session.add(HabitLog(habit_id=habit.id, completed_date=TODAY))
    await db_session.flush()

    impact = (
        await insights_service.habit_mood_impact(db_session, user.id, start, TODAY)
    )[0]

    assert impact.days_done == 1
    assert impact.days_missed == 0
    assert impact.mood_when_done == 5.0


# --------------------------------------------------------------------------
# Weekday grouping - the dialect-sensitive one
# --------------------------------------------------------------------------

async def test_weekday_returns_all_seven_days_monday_first(db_session, user):
    weekdays = await insights_service.weekday_mood(
        db_session, user.id, TODAY - timedelta(days=6), TODAY
    )

    assert [w.weekday for w in weekdays] == list(range(7))
    assert weekdays[0].label == "Monday"
    assert weekdays[6].label == "Sunday"
    # No check-ins: every day present, all empty.
    assert all(w.avg_mood is None and w.checkins == 0 for w in weekdays)


async def test_weekday_puts_a_checkin_on_the_right_day_of_week(db_session, user):
    """
    The rotation from the database's own weekday numbering to Monday-first
    is the part most likely to be off by one, and it differs per dialect.
    """
    # A known Monday, and the Wednesday two days later.
    monday = date(2026, 8, 31)
    assert monday.weekday() == 0

    await _checkin(db_session, user, monday, 5, energy=4)
    await _checkin(db_session, user, monday + timedelta(days=2), 1, energy=2)
    await db_session.flush()

    weekdays = await insights_service.weekday_mood(
        db_session, user.id, monday, monday + timedelta(days=6)
    )
    by_label = {w.label: w for w in weekdays}

    assert by_label["Monday"].avg_mood == 5.0
    assert by_label["Monday"].avg_energy == 4.0
    assert by_label["Monday"].checkins == 1
    assert by_label["Wednesday"].avg_mood == 1.0
    assert by_label["Wednesday"].checkins == 1
    assert by_label["Tuesday"].avg_mood is None


async def test_weekday_averages_repeats_of_the_same_day(db_session, user):
    monday = date(2026, 8, 31)
    await _checkin(db_session, user, monday, 2)
    await _checkin(db_session, user, monday + timedelta(days=7), 4)
    await db_session.flush()

    weekdays = await insights_service.weekday_mood(
        db_session, user.id, monday, monday + timedelta(days=13)
    )
    monday_row = next(w for w in weekdays if w.label == "Monday")

    assert monday_row.checkins == 2
    assert monday_row.avg_mood == 3.0


# --------------------------------------------------------------------------
# Distribution and tags
# --------------------------------------------------------------------------

async def test_distribution_reports_every_score_including_empty_ones(db_session, user):
    start = TODAY - timedelta(days=2)
    await _checkin(db_session, user, start, 3)
    await _checkin(db_session, user, start + timedelta(days=1), 3)
    await _checkin(db_session, user, TODAY, 5)
    await db_session.flush()

    buckets = await insights_service.mood_distribution(db_session, user.id, start, TODAY)

    assert [b.score for b in buckets] == [1, 2, 3, 4, 5]
    assert {b.score: b.count for b in buckets} == {1: 0, 2: 0, 3: 2, 4: 0, 5: 1}


async def test_tag_mood_averages_the_mood_of_the_days_a_tag_was_written_on(
    db_session, user
):
    start = TODAY - timedelta(days=2)
    tag = Tag(user_id=user.id, name="work", color="#ffffff")
    db_session.add(tag)
    await db_session.flush()

    for offset, mood in enumerate([2, 4]):
        day = start + timedelta(days=offset)
        await _checkin(db_session, user, day, mood)
        created = datetime.combine(day, datetime.min.time(), tzinfo=timezone.utc)
        entry = JournalEntry(
            user_id=user.id,
            title=f"entry {offset}",
            content="...",
            created_at=created,
            updated_at=created,
        )
        entry.tags = [tag]
        db_session.add(entry)
    await db_session.flush()

    rows = await insights_service.tag_mood(db_session, user.id, start, TODAY)

    assert len(rows) == 1
    assert rows[0].name == "work"
    assert rows[0].entries == 2
    assert rows[0].avg_mood == 3.0


async def test_tag_mood_keeps_entries_written_on_days_with_no_checkin(db_session, user):
    """
    The join to check-ins is a LEFT join: an untracked day still counts as an
    entry, it just contributes nothing to the average.
    """
    day = TODAY - timedelta(days=1)
    tag = Tag(user_id=user.id, name="quiet", color="#ffffff")
    db_session.add(tag)
    await db_session.flush()

    created = datetime.combine(day, datetime.min.time(), tzinfo=timezone.utc)
    entry = JournalEntry(
        user_id=user.id,
        title="no check-in that day",
        content="...",
        created_at=created,
        updated_at=created,
    )
    entry.tags = [tag]
    db_session.add(entry)
    await db_session.flush()

    rows = await insights_service.tag_mood(db_session, user.id, day, TODAY)

    assert rows[0].entries == 1
    assert rows[0].avg_mood is None


# --------------------------------------------------------------------------
# Assembly and the headline
# --------------------------------------------------------------------------

async def test_summary_on_an_empty_account_is_shaped_but_empty(db_session, user):
    summary = await insights_service.build_summary(db_session, user.id, days=30)

    assert summary.range_days == 30
    assert summary.habit_impact == []
    assert summary.tag_mood == []
    assert len(summary.weekday) == 7
    assert len(summary.mood_distribution) == 5
    assert summary.headline is None
    assert summary.best_weekday is None


async def test_headline_names_the_habit_with_the_strongest_effect(db_session, user):
    """
    Ten alternating days: kept on the 5s, missed on the 3s. Both sides clear
    MIN_DAYS_FOR_SIGNAL, so the habit gets the headline.
    """
    start = TODAY - timedelta(days=9)
    habit = await _habit(db_session, user, "Sleep by 11pm", created=start)

    for offset in range(10):
        day = start + timedelta(days=offset)
        kept = offset % 2 == 0
        await _checkin(db_session, user, day, 5 if kept else 3)
        if kept:
            db_session.add(HabitLog(habit_id=habit.id, completed_date=day))
    await db_session.flush()

    summary = await insights_service.build_summary(db_session, user.id, days=10)

    assert summary.headline is not None
    assert "Sleep by 11pm" in summary.headline
    assert "higher" in summary.headline


async def test_headline_stays_silent_when_the_evidence_is_thin(db_session, user):
    """
    Two days on each side is a coin flip, not a finding. The numbers are
    still reported; only the claim is withheld.
    """
    start = TODAY - timedelta(days=3)
    habit = await _habit(db_session, user, "Barely tracked", created=start)

    for offset, mood in enumerate([5, 5, 1, 1]):
        day = start + timedelta(days=offset)
        await _checkin(db_session, user, day, mood)
        if mood == 5:
            db_session.add(HabitLog(habit_id=habit.id, completed_date=day))
    await db_session.flush()

    summary = await insights_service.build_summary(db_session, user.id, days=4)

    assert summary.habit_impact[0].delta == 4.0
    assert summary.headline is None
