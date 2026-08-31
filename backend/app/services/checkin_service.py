"""
Check-in service: one mood/energy entry per user per day.

The "one per day" rule is a database constraint (uq_checkins_user_date),
so create_or_update deliberately reads-then-writes rather than blindly
inserting: an upsert here keeps the API idempotent for the same day.
"""

from datetime import date, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.wellness import CheckIn
from app.schemas.wellness import CheckInCreate, CheckInUpdate


async def get_by_date(
    db: AsyncSession,
    user_id: UUID,
    on: date,
) -> Optional[CheckIn]:
    """Fetch the user's check-in for a specific day, if it exists."""
    result = await db.execute(
        select(CheckIn).where(
            CheckIn.user_id == user_id,
            CheckIn.checkin_date == on,
        )
    )
    return result.scalar_one_or_none()


async def list_range(
    db: AsyncSession,
    user_id: UUID,
    start: date,
    end: date,
) -> list[CheckIn]:
    """
    Fetch check-ins in an inclusive date range, oldest first.

    Ordering is done in SQL so the frontend can render the trend line
    without re-sorting.
    """
    result = await db.execute(
        select(CheckIn)
        .where(
            CheckIn.user_id == user_id,
            CheckIn.checkin_date >= start,
            CheckIn.checkin_date <= end,
        )
        .order_by(CheckIn.checkin_date.asc())
    )
    return list(result.scalars().all())


async def list_recent(
    db: AsyncSession,
    user_id: UUID,
    days: int = 30,
) -> list[CheckIn]:
    """Fetch the last N days of check-ins, oldest first."""
    end = date.today()
    start = end - timedelta(days=days - 1)
    return await list_range(db, user_id, start, end)


async def create_or_update(
    db: AsyncSession,
    user_id: UUID,
    data: CheckInCreate,
) -> CheckIn:
    """
    Record the check-in for a day, overwriting one that already exists.

    Submitting twice for the same day updates it rather than failing,
    which is what a user re-rating their day actually expects.
    """
    on = data.checkin_date or date.today()
    existing = await get_by_date(db, user_id, on)

    if existing:
        existing.mood_score = data.mood_score
        existing.energy_score = data.energy_score
        existing.note = data.note
        await db.flush()
        await db.refresh(existing)
        return existing

    checkin = CheckIn(
        user_id=user_id,
        mood_score=data.mood_score,
        energy_score=data.energy_score,
        note=data.note,
        checkin_date=on,
    )
    db.add(checkin)
    await db.flush()
    await db.refresh(checkin)
    return checkin


async def update(
    db: AsyncSession,
    user_id: UUID,
    checkin_id: UUID,
    data: CheckInUpdate,
) -> CheckIn:
    """
    Patch an existing check-in.

    Raises:
        NotFoundError: If the check-in does not exist or belongs to someone else.
    """
    result = await db.execute(
        select(CheckIn).where(
            CheckIn.id == checkin_id,
            CheckIn.user_id == user_id,
        )
    )
    checkin = result.scalar_one_or_none()
    if not checkin:
        raise NotFoundError("Check-in not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(checkin, field, value)

    await db.flush()
    await db.refresh(checkin)
    return checkin


async def delete(db: AsyncSession, user_id: UUID, checkin_id: UUID) -> None:
    """
    Delete a check-in.

    Raises:
        NotFoundError: If the check-in does not exist or belongs to someone else.
    """
    result = await db.execute(
        select(CheckIn).where(
            CheckIn.id == checkin_id,
            CheckIn.user_id == user_id,
        )
    )
    checkin = result.scalar_one_or_none()
    if not checkin:
        raise NotFoundError("Check-in not found")

    await db.delete(checkin)
    await db.flush()
