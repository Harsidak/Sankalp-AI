"""
Tests for the wellness domain: check-ins, tags, journal, habits, dashboard.

These exercise the service layer against a real (SQLite) database rather
than mocking it, because the behaviour worth testing here -- upserts,
cascade deletes, join-table replacement, GROUP BY aggregates -- lives in
the database, and a mock would assert nothing about it.
"""

from datetime import date, timedelta

import pytest
from sqlalchemy import func, select

from app.models.user import AuthProvider, User
from app.models.wellness import (
    CheckIn,
    EntryTag,
    Habit,
    HabitLog,
    JournalEntry,
    Tag,
)
from app.schemas.wellness import (
    CheckInCreate,
    HabitCreate,
    JournalCreate,
    JournalUpdate,
    TagCreate,
)
from app.services import (
    checkin_service,
    dashboard_service,
    habit_service,
    journal_service,
    tag_service,
)

TODAY = date.today()


@pytest.fixture
async def user(db_session) -> User:
    """A saved user to hang wellness data off."""
    u = User(
        email="wellness@test.dev",
        hashed_password="not-a-real-hash",
        auth_provider=AuthProvider.LOCAL,
    )
    db_session.add(u)
    await db_session.flush()
    return u


# --------------------------------------------------------------------------
# Streak maths - pure functions, no database
# --------------------------------------------------------------------------

def test_streak_of_nothing_is_zero():
    assert habit_service.compute_current_streak([], TODAY) == 0
    assert habit_service.compute_longest_streak([]) == 0


def test_current_streak_counts_back_from_today():
    days = [TODAY - timedelta(days=d) for d in range(4)]
    assert habit_service.compute_current_streak(days, TODAY) == 4


def test_yesterday_anchors_the_streak():
    """An unfinished today must not read as a broken streak."""
    days = [TODAY - timedelta(days=d) for d in (1, 2, 3)]
    assert habit_service.compute_current_streak(days, TODAY) == 3


def test_streak_breaks_after_a_missed_day():
    days = [TODAY - timedelta(days=d) for d in (2, 3, 4)]
    assert habit_service.compute_current_streak(days, TODAY) == 0


def test_longest_streak_is_independent_of_current():
    days = [TODAY - timedelta(days=d) for d in (0, 1, 2, 5, 6, 7, 8)]
    assert habit_service.compute_current_streak(days, TODAY) == 3
    assert habit_service.compute_longest_streak(days) == 4


def test_duplicate_days_do_not_inflate_a_streak():
    days = [TODAY, TODAY, TODAY - timedelta(days=1)]
    assert habit_service.compute_current_streak(days, TODAY) == 2


# --------------------------------------------------------------------------
# Check-ins
# --------------------------------------------------------------------------

async def test_second_checkin_same_day_updates_rather_than_duplicates(db_session, user):
    """UNIQUE(user_id, checkin_date) means re-rating a day overwrites it."""
    await checkin_service.create_or_update(
        db_session, user.id, CheckInCreate(mood_score=4, energy_score=3)
    )
    updated = await checkin_service.create_or_update(
        db_session, user.id, CheckInCreate(mood_score=2, energy_score=2)
    )

    rows = await checkin_service.list_recent(db_session, user.id, days=7)
    assert len(rows) == 1
    assert updated.mood_score == 2


async def test_list_range_is_inclusive_and_ordered(db_session, user):
    for offset in (3, 1, 2):
        await checkin_service.create_or_update(
            db_session,
            user.id,
            CheckInCreate(
                mood_score=3,
                energy_score=3,
                checkin_date=TODAY - timedelta(days=offset),
            ),
        )

    rows = await checkin_service.list_range(
        db_session, user.id, TODAY - timedelta(days=3), TODAY - timedelta(days=1)
    )
    assert len(rows) == 3
    assert [r.checkin_date for r in rows] == sorted(r.checkin_date for r in rows)


async def test_future_checkin_is_rejected():
    with pytest.raises(ValueError):
        CheckInCreate(
            mood_score=3,
            energy_score=3,
            checkin_date=TODAY + timedelta(days=1),
        )


@pytest.mark.parametrize("score", [0, 6, -1])
async def test_out_of_range_mood_is_rejected(score):
    with pytest.raises(ValueError):
        CheckInCreate(mood_score=score, energy_score=3)


# --------------------------------------------------------------------------
# Tags
# --------------------------------------------------------------------------

async def test_tag_names_are_normalized(db_session, user):
    tag = await tag_service.create(db_session, user.id, TagCreate(name="  Study  "))
    assert tag.name == "study"


async def test_duplicate_tag_name_is_rejected(db_session, user):
    await tag_service.create(db_session, user.id, TagCreate(name="study"))
    with pytest.raises(Exception, match="already have a tag"):
        await tag_service.create(db_session, user.id, TagCreate(name="STUDY"))


async def test_tag_counts_include_unused_tags(db_session, user):
    """The LEFT OUTER JOIN must keep tags that no entry carries."""
    await tag_service.create(db_session, user.id, TagCreate(name="used"))
    await tag_service.create(db_session, user.id, TagCreate(name="unused"))
    tags = await tag_service.list_all(db_session, user.id)
    used = next(t for t in tags if t.name == "used")

    await journal_service.create(
        db_session,
        user.id,
        JournalCreate(title="t", content="c", tag_ids=[str(used.id)]),
    )

    counts = {
        tag.name: count
        for tag, count in await tag_service.list_with_counts(db_session, user.id)
    }
    assert counts == {"used": 1, "unused": 0}


# --------------------------------------------------------------------------
# Journal
# --------------------------------------------------------------------------

async def test_entry_carries_its_tags(db_session, user):
    a = await tag_service.create(db_session, user.id, TagCreate(name="a"))
    b = await tag_service.create(db_session, user.id, TagCreate(name="b"))

    entry = await journal_service.create(
        db_session,
        user.id,
        JournalCreate(title="Two tags", content="body", tag_ids=[str(a.id), str(b.id)]),
    )
    assert {t.name for t in entry.tags} == {"a", "b"}


async def test_update_replaces_the_whole_tag_set(db_session, user):
    a = await tag_service.create(db_session, user.id, TagCreate(name="a"))
    b = await tag_service.create(db_session, user.id, TagCreate(name="b"))
    entry = await journal_service.create(
        db_session,
        user.id,
        JournalCreate(title="t", content="c", tag_ids=[str(a.id), str(b.id)]),
    )

    entry = await journal_service.update(
        db_session, user.id, entry.id, JournalUpdate(tag_ids=[str(a.id)])
    )
    assert {t.name for t in entry.tags} == {"a"}


async def test_omitting_tag_ids_leaves_tags_alone(db_session, user):
    a = await tag_service.create(db_session, user.id, TagCreate(name="a"))
    entry = await journal_service.create(
        db_session, user.id, JournalCreate(title="t", content="c", tag_ids=[str(a.id)])
    )

    entry = await journal_service.update(
        db_session, user.id, entry.id, JournalUpdate(title="renamed")
    )
    assert entry.title == "renamed"
    assert {t.name for t in entry.tags} == {"a"}


async def test_unknown_tag_ids_are_ignored_not_fatal(db_session, user):
    """A stale chip in the UI should not cost the user their entry."""
    entry = await journal_service.create(
        db_session,
        user.id,
        JournalCreate(
            title="t",
            content="c",
            tag_ids=["not-a-uuid", "11111111-1111-1111-1111-111111111111"],
        ),
    )
    assert entry.tags == []


async def test_search_matches_title_and_content(db_session, user):
    await journal_service.create(
        db_session, user.id, JournalCreate(title="Lab day", content="the join clicked")
    )
    await journal_service.create(
        db_session, user.id, JournalCreate(title="Quiet", content="cooked properly")
    )

    _, by_content = await journal_service.list_entries(db_session, user.id, search="join")
    _, by_title = await journal_service.list_entries(db_session, user.id, search="Quiet")
    _, neither = await journal_service.list_entries(db_session, user.id, search="zzz")
    assert (by_content, by_title, neither) == (1, 1, 0)


async def test_tag_filter_matches_any_of_the_given_tags(db_session, user):
    a = await tag_service.create(db_session, user.id, TagCreate(name="a"))
    b = await tag_service.create(db_session, user.id, TagCreate(name="b"))
    await journal_service.create(
        db_session, user.id, JournalCreate(title="1", content="x", tag_ids=[str(a.id)])
    )
    await journal_service.create(
        db_session, user.id, JournalCreate(title="2", content="y", tag_ids=[str(b.id)])
    )
    await journal_service.create(db_session, user.id, JournalCreate(title="3", content="z"))

    _, total = await journal_service.list_entries(
        db_session, user.id, tag_ids=[a.id, b.id]
    )
    assert total == 2


async def test_one_user_cannot_read_another_users_entry(db_session, user):
    other = User(email="other@test.dev", auth_provider=AuthProvider.LOCAL)
    db_session.add(other)
    await db_session.flush()

    entry = await journal_service.create(
        db_session, other.id, JournalCreate(title="private", content="secret")
    )

    with pytest.raises(Exception, match="not found"):
        await journal_service.get_owned(db_session, user.id, entry.id)


# --------------------------------------------------------------------------
# Habits
# --------------------------------------------------------------------------

async def test_toggle_marks_then_unmarks_a_day(db_session, user):
    habit = await habit_service.create(db_session, user.id, HabitCreate(name="Walk"))

    _, _, completed = await habit_service.toggle_log(db_session, user.id, habit.id)
    assert completed is True

    _, _, completed = await habit_service.toggle_log(db_session, user.id, habit.id)
    assert completed is False

    refreshed = await habit_service.get_owned(db_session, user.id, habit.id)
    assert refreshed.logs == []


async def test_habit_summary_reports_streaks(db_session, user):
    habit = await habit_service.create(db_session, user.id, HabitCreate(name="Read"))
    for offset in range(3):
        await habit_service.toggle_log(
            db_session, user.id, habit.id, TODAY - timedelta(days=offset)
        )

    summary = habit_service.summarize(
        await habit_service.get_owned(db_session, user.id, habit.id)
    )
    assert summary["current_streak"] == 3
    assert summary["completed_today"] is True
    assert len(summary["completed_dates"]) == 3


async def test_archived_habits_are_hidden_by_default(db_session, user):
    from app.schemas.wellness import HabitUpdate

    habit = await habit_service.create(db_session, user.id, HabitCreate(name="Old"))
    await habit_service.update(
        db_session, user.id, habit.id, HabitUpdate(is_archived=True)
    )

    assert await habit_service.list_habits(db_session, user.id) == []
    assert len(await habit_service.list_habits(db_session, user.id, include_archived=True)) == 1


# --------------------------------------------------------------------------
# Dashboard aggregates
# --------------------------------------------------------------------------

async def test_mood_trend_fills_gaps_with_nulls(db_session, user):
    """Missing days must stay null so the chart breaks the line."""
    await checkin_service.create_or_update(
        db_session, user.id, CheckInCreate(mood_score=4, energy_score=4)
    )

    summary = await dashboard_service.build_summary(db_session, user.id, days=30)
    assert len(summary.mood_trend) == 30
    assert sum(1 for p in summary.mood_trend if p.mood is None) == 29
    assert summary.mood_trend[-1].mood == 4.0


async def test_summary_counts_and_averages(db_session, user):
    for offset, mood in enumerate([2, 4]):
        await checkin_service.create_or_update(
            db_session,
            user.id,
            CheckInCreate(
                mood_score=mood,
                energy_score=3,
                checkin_date=TODAY - timedelta(days=offset),
            ),
        )
    await journal_service.create(db_session, user.id, JournalCreate(title="t", content="c"))

    summary = await dashboard_service.build_summary(db_session, user.id, days=30)
    assert summary.checkin_count == 2
    assert summary.average_mood == 3.0
    assert summary.journal_count == 1


async def test_habits_with_no_completions_still_appear(db_session, user):
    """The LEFT OUTER JOIN keeps the habits the user most needs to see."""
    await habit_service.create(db_session, user.id, HabitCreate(name="Never done"))

    summary = await dashboard_service.build_summary(db_session, user.id, days=30)
    assert len(summary.habit_completions) == 1
    assert summary.habit_completions[0].completions == 0


async def test_empty_account_produces_an_empty_summary(db_session, user):
    summary = await dashboard_service.build_summary(db_session, user.id, days=30)
    assert summary.average_mood is None
    assert summary.checkin_count == 0
    assert summary.top_tags == []
    assert summary.longest_active_streak == 0


# --------------------------------------------------------------------------
# Referential integrity
# --------------------------------------------------------------------------

async def test_deleting_a_user_cascades_to_every_child_table(db_session, user):
    tag = await tag_service.create(db_session, user.id, TagCreate(name="a"))
    await journal_service.create(
        db_session, user.id, JournalCreate(title="t", content="c", tag_ids=[str(tag.id)])
    )
    await checkin_service.create_or_update(
        db_session, user.id, CheckInCreate(mood_score=3, energy_score=3)
    )
    habit = await habit_service.create(db_session, user.id, HabitCreate(name="Walk"))
    await habit_service.toggle_log(db_session, user.id, habit.id)

    await db_session.delete(user)
    await db_session.flush()

    for model in (CheckIn, JournalEntry, Tag, Habit, HabitLog, EntryTag):
        count = (
            await db_session.execute(select(func.count()).select_from(model))
        ).scalar_one()
        assert count == 0, f"{model.__name__} kept {count} orphan rows"


async def test_deleting_a_tag_keeps_the_entry(db_session, user):
    """The cascade runs across entry_tags, not journal_entries."""
    tag = await tag_service.create(db_session, user.id, TagCreate(name="a"))
    entry = await journal_service.create(
        db_session, user.id, JournalCreate(title="t", content="c", tag_ids=[str(tag.id)])
    )

    await tag_service.delete(db_session, user.id, tag.id)

    survivor = await journal_service.get_owned(db_session, user.id, entry.id)
    assert survivor.tags == []
