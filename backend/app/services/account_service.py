"""
Account service: whole-account export and deletion.

Deletion here is a real DELETE, not a flag. Every wellness table declares
ON DELETE CASCADE against users.id, so removing the user row removes the
check-ins, journal entries, tags, habits, habit logs, entry_tags rows,
chat sessions and refresh tokens with it -- in one statement, enforced by
the database rather than by a sequence of service calls that could be
interrupted half way. `count_owned_rows` is taken *before* the delete so
the API can report what the cascade removed.

`user_service.soft_delete_user` still exists for deactivation, which is a
different thing: it keeps the data and locks the account.
"""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import AuthenticationError, ValidationError
from app.core.security import verify_password
from app.models.chat import ChatSession
from app.models.user import AuthProvider, RefreshToken, User
from app.models.wellness import (
    CheckIn,
    EntryTag,
    Habit,
    HabitLog,
    JournalEntry,
    Tag,
)
from app.schemas.account import (
    AccountExport,
    DeleteAccountRequest,
    ExportedCheckIn,
    ExportedHabit,
    ExportedJournalEntry,
    ExportedTag,
)


async def count_owned_rows(db: AsyncSession, user_id: UUID) -> dict[str, int]:
    """
    Row counts per table for one user.

    The two join tables are counted through their parent, because neither
    carries a user_id of its own -- which is the correct design, and the
    reason the counts need a join rather than a filter.
    """
    async def scalar(stmt) -> int:
        return int((await db.execute(stmt)).scalar_one() or 0)

    return {
        "checkins": await scalar(
            select(func.count(CheckIn.id)).where(CheckIn.user_id == user_id)
        ),
        "journal_entries": await scalar(
            select(func.count(JournalEntry.id)).where(JournalEntry.user_id == user_id)
        ),
        "tags": await scalar(select(func.count(Tag.id)).where(Tag.user_id == user_id)),
        "habits": await scalar(
            select(func.count(Habit.id)).where(Habit.user_id == user_id)
        ),
        "habit_logs": await scalar(
            select(func.count(HabitLog.id))
            .select_from(HabitLog)
            .join(Habit, Habit.id == HabitLog.habit_id)
            .where(Habit.user_id == user_id)
        ),
        "entry_tags": await scalar(
            select(func.count())
            .select_from(EntryTag)
            .join(JournalEntry, JournalEntry.id == EntryTag.entry_id)
            .where(JournalEntry.user_id == user_id)
        ),
        "chat_sessions": await scalar(
            select(func.count(ChatSession.id)).where(ChatSession.user_id == user_id)
        ),
        "refresh_tokens": await scalar(
            select(func.count(RefreshToken.id)).where(RefreshToken.user_id == user_id)
        ),
    }


async def export_account(db: AsyncSession, user: User) -> AccountExport:
    """
    Gather everything the account owns into one document.

    Journal entries load their tags eagerly and habits their logs, so this
    is four queries plus their eager loads rather than one per row.
    """
    checkins = (
        await db.execute(
            select(CheckIn)
            .where(CheckIn.user_id == user.id)
            .order_by(CheckIn.checkin_date.asc())
        )
    ).scalars().all()

    entries = (
        await db.execute(
            select(JournalEntry)
            .where(JournalEntry.user_id == user.id)
            .options(selectinload(JournalEntry.tags))
            .order_by(JournalEntry.created_at.asc())
        )
    ).scalars().unique().all()

    habits = (
        await db.execute(
            select(Habit)
            .where(Habit.user_id == user.id)
            .options(selectinload(Habit.logs))
            .order_by(Habit.created_at.asc())
        )
    ).scalars().unique().all()

    tags = (
        await db.execute(
            select(Tag).where(Tag.user_id == user.id).order_by(Tag.name.asc())
        )
    ).scalars().all()

    return AccountExport(
        exported_at=datetime.now(timezone.utc),
        email=user.email,
        full_name=user.full_name,
        member_since=user.created_at,
        checkins=[
            ExportedCheckIn(
                checkin_date=c.checkin_date,
                mood_score=c.mood_score,
                energy_score=c.energy_score,
                note=c.note,
            )
            for c in checkins
        ],
        journal_entries=[
            ExportedJournalEntry(
                title=e.title,
                content=e.content,
                tags=sorted(t.name for t in e.tags),
                created_at=e.created_at,
                updated_at=e.updated_at,
            )
            for e in entries
        ],
        habits=[
            ExportedHabit(
                name=h.name,
                color=h.color,
                target_per_week=h.target_per_week,
                is_archived=h.is_archived,
                completed_dates=sorted(log.completed_date for log in h.logs),
            )
            for h in habits
        ],
        tags=[ExportedTag(name=t.name, color=t.color) for t in tags],
        counts=await count_owned_rows(db, user.id),
    )


async def delete_account(
    db: AsyncSession,
    user: User,
    data: DeleteAccountRequest,
) -> dict[str, int]:
    """
    Permanently delete the account and everything cascading from it.

    Returns:
        The row counts removed, captured before the delete.

    Raises:
        ValidationError: If the confirmation phrase is wrong, or a password
            account supplied no password.
        AuthenticationError: If the supplied password does not match.
    """
    if data.confirm != "DELETE":
        raise ValidationError("Type DELETE to confirm account deletion")

    # OAuth-only accounts have no password to verify; the confirmation
    # phrase is the whole check for them.
    if user.hashed_password:
        if not data.password:
            raise ValidationError("Your current password is required to delete the account")
        if not verify_password(data.password, user.hashed_password):
            raise AuthenticationError("Password is incorrect")
    elif user.auth_provider != AuthProvider.GOOGLE:  # pragma: no cover - defensive
        raise ValidationError("This account cannot be deleted automatically")

    removed = await count_owned_rows(db, user.id)

    await db.delete(user)
    await db.flush()

    return removed
