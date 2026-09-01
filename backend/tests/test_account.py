"""
Tests for whole-account export and deletion.

The deletion tests are the ones that matter: they assert that removing the
user row removes every dependent row, which is a claim about the schema's
ON DELETE CASCADE rules rather than about the service. conftest turns on
`PRAGMA foreign_keys` precisely so these cannot pass for the wrong reason.
"""

from datetime import date, datetime, timedelta, timezone

import pytest
from sqlalchemy import func, select

from app.core.exceptions import AuthenticationError, ValidationError
from app.core.security import hash_password
from app.models.user import AuthProvider, RefreshToken, User
from app.models.wellness import (
    CheckIn,
    EntryTag,
    Habit,
    HabitLog,
    JournalEntry,
    Tag,
)
from app.schemas.account import DeleteAccountRequest
from app.services import account_service

TODAY = date.today()
PASSWORD = "correct-horse-battery"


@pytest.fixture
async def user(db_session) -> User:
    """A password account with one row in every table that hangs off users."""
    u = User(
        email="account@test.dev",
        full_name="Account Holder",
        hashed_password=hash_password(PASSWORD),
        auth_provider=AuthProvider.LOCAL,
    )
    db_session.add(u)
    await db_session.flush()

    db_session.add(
        CheckIn(user_id=u.id, checkin_date=TODAY, mood_score=4, energy_score=3, note="ok")
    )

    tag = Tag(user_id=u.id, name="work", color="#6366f1")
    db_session.add(tag)
    await db_session.flush()

    created = datetime.combine(TODAY, datetime.min.time(), tzinfo=timezone.utc)
    entry = JournalEntry(
        user_id=u.id,
        title="Day one",
        content="Testing the cascade.",
        created_at=created,
        updated_at=created,
    )
    entry.tags = [tag]
    db_session.add(entry)

    habit = Habit(user_id=u.id, name="Walk", color="#10b981", target_per_week=5)
    db_session.add(habit)
    await db_session.flush()
    db_session.add(HabitLog(habit_id=habit.id, completed_date=TODAY))

    db_session.add(
        RefreshToken(
            token_hash="a-hash",
            user_id=u.id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
    )
    await db_session.flush()
    return u


# --------------------------------------------------------------------------
# Export
# --------------------------------------------------------------------------

async def test_export_carries_every_table(db_session, user):
    export = await account_service.export_account(db_session, user)

    assert export.email == "account@test.dev"
    assert export.full_name == "Account Holder"
    assert len(export.checkins) == 1
    assert len(export.journal_entries) == 1
    assert len(export.habits) == 1
    assert len(export.tags) == 1


async def test_export_resolves_tags_and_logs_rather_than_ids(db_session, user):
    """
    An export is for a human, so the many-to-many is flattened to tag names
    and the habit's logs to the dates themselves.
    """
    export = await account_service.export_account(db_session, user)

    assert export.journal_entries[0].tags == ["work"]
    assert export.habits[0].completed_dates == [TODAY]


async def test_export_counts_match_the_rows_returned(db_session, user):
    export = await account_service.export_account(db_session, user)

    assert export.counts["checkins"] == len(export.checkins)
    assert export.counts["journal_entries"] == len(export.journal_entries)
    assert export.counts["habits"] == len(export.habits)
    assert export.counts["tags"] == len(export.tags)
    # Counted through their parents, since neither join table has a user_id.
    assert export.counts["entry_tags"] == 1
    assert export.counts["habit_logs"] == 1


async def test_export_of_an_empty_account_is_empty_not_missing(db_session):
    fresh = User(
        email="empty@test.dev",
        hashed_password=hash_password(PASSWORD),
        auth_provider=AuthProvider.LOCAL,
    )
    db_session.add(fresh)
    await db_session.flush()

    export = await account_service.export_account(db_session, fresh)

    assert export.checkins == []
    assert export.journal_entries == []
    assert all(count == 0 for count in export.counts.values())


async def test_export_does_not_include_another_users_rows(db_session, user):
    other = User(
        email="stranger@test.dev",
        hashed_password=hash_password(PASSWORD),
        auth_provider=AuthProvider.LOCAL,
    )
    db_session.add(other)
    await db_session.flush()
    db_session.add(
        CheckIn(user_id=other.id, checkin_date=TODAY, mood_score=1, energy_score=1)
    )
    await db_session.flush()

    export = await account_service.export_account(db_session, user)

    assert len(export.checkins) == 1
    assert export.checkins[0].mood_score == 4


# --------------------------------------------------------------------------
# Deletion - confirmation guards
# --------------------------------------------------------------------------

async def test_delete_refuses_without_the_confirmation_phrase(db_session, user):
    with pytest.raises(ValidationError):
        await account_service.delete_account(
            db_session, user, DeleteAccountRequest(password=PASSWORD, confirm="delete")
        )

    assert await db_session.get(User, user.id) is not None


async def test_delete_refuses_a_wrong_password(db_session, user):
    with pytest.raises(AuthenticationError):
        await account_service.delete_account(
            db_session, user, DeleteAccountRequest(password="nope", confirm="DELETE")
        )

    assert await db_session.get(User, user.id) is not None


async def test_delete_refuses_a_password_account_with_no_password_supplied(
    db_session, user
):
    with pytest.raises(ValidationError):
        await account_service.delete_account(
            db_session, user, DeleteAccountRequest(confirm="DELETE")
        )


async def test_google_account_deletes_on_the_phrase_alone(db_session):
    """An OAuth-only account has no password to check."""
    google_user = User(
        email="google@test.dev",
        hashed_password=None,
        google_id="g-123",
        auth_provider=AuthProvider.GOOGLE,
    )
    db_session.add(google_user)
    await db_session.flush()

    await account_service.delete_account(
        db_session, google_user, DeleteAccountRequest(confirm="DELETE")
    )

    assert await db_session.get(User, google_user.id) is None


# --------------------------------------------------------------------------
# Deletion - the cascade itself
# --------------------------------------------------------------------------

async def test_delete_removes_the_user_and_reports_what_went_with_it(db_session, user):
    removed = await account_service.delete_account(
        db_session, user, DeleteAccountRequest(password=PASSWORD, confirm="DELETE")
    )

    assert await db_session.get(User, user.id) is None
    assert removed == {
        "checkins": 1,
        "journal_entries": 1,
        "tags": 1,
        "habits": 1,
        "habit_logs": 1,
        "entry_tags": 1,
        "chat_sessions": 0,
        "refresh_tokens": 1,
    }


async def test_delete_cascades_to_every_dependent_table(db_session, user):
    """
    The point of the schema: one DELETE against users empties everything
    below it, because the database enforces it -- not the service.
    """
    await account_service.delete_account(
        db_session, user, DeleteAccountRequest(password=PASSWORD, confirm="DELETE")
    )

    async def count(model) -> int:
        return int((await db_session.execute(select(func.count()).select_from(model))).scalar_one())

    assert await count(CheckIn) == 0
    assert await count(JournalEntry) == 0
    assert await count(Tag) == 0
    assert await count(Habit) == 0
    assert await count(HabitLog) == 0
    assert await count(EntryTag) == 0
    assert await count(RefreshToken) == 0


async def test_delete_leaves_other_accounts_untouched(db_session, user):
    survivor = User(
        email="survivor@test.dev",
        hashed_password=hash_password(PASSWORD),
        auth_provider=AuthProvider.LOCAL,
    )
    db_session.add(survivor)
    await db_session.flush()
    db_session.add(
        CheckIn(user_id=survivor.id, checkin_date=TODAY, mood_score=5, energy_score=5)
    )
    await db_session.flush()

    await account_service.delete_account(
        db_session, user, DeleteAccountRequest(password=PASSWORD, confirm="DELETE")
    )

    assert await db_session.get(User, survivor.id) is not None
    remaining = (await db_session.execute(select(CheckIn))).scalars().all()
    assert len(remaining) == 1
    assert remaining[0].user_id == survivor.id
