"""
Daily check-in router.

All endpoints are user-scoped: the authenticated user's id is taken from
the token, never from the request body, so one user cannot read or write
another user's check-ins.
"""

from datetime import date, timedelta
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.common import APIResponse
from app.schemas.wellness import CheckInCreate, CheckInRead, CheckInUpdate
from app.services import checkin_service

router = APIRouter(prefix="/checkins", tags=["Check-ins"])


def _serialize(checkin) -> CheckInRead:
    return CheckInRead(
        id=str(checkin.id),
        mood_score=checkin.mood_score,
        energy_score=checkin.energy_score,
        note=checkin.note,
        checkin_date=checkin.checkin_date,
        created_at=checkin.created_at,
    )


@router.get(
    "",
    response_model=APIResponse[list[CheckInRead]],
    summary="List check-ins in a date range",
)
async def list_checkins(
    start: Optional[date] = Query(None, description="Inclusive start date"),
    end: Optional[date] = Query(None, description="Inclusive end date"),
    days: int = Query(30, ge=1, le=365, description="Used when start/end are omitted"),
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List check-ins, oldest first.

    Give an explicit start/end range, or omit both to get the last N days.
    """
    if start and end:
        checkins = await checkin_service.list_range(db, user.id, start, end)
    else:
        checkins = await checkin_service.list_recent(db, user.id, days)

    return APIResponse(success=True, data=[_serialize(c) for c in checkins])


@router.get(
    "/today",
    response_model=APIResponse[Optional[CheckInRead]],
    summary="Get today's check-in",
)
async def get_today(
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Fetch today's check-in, or null if the user has not checked in yet.

    Returning null rather than 404 lets the UI treat "not yet done" as a
    normal state instead of an error path.
    """
    checkin = await checkin_service.get_by_date(db, user.id, date.today())
    return APIResponse(
        success=True,
        data=_serialize(checkin) if checkin else None,
    )


@router.get(
    "/streak",
    response_model=APIResponse[dict],
    summary="Consecutive check-in days",
)
async def get_streak(
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    The current run of consecutive check-in days, anchored on today or
    yesterday so an unfinished today does not read as a broken streak, plus
    the longest run anywhere in the last year.
    """
    checkins = await checkin_service.list_recent(db, user.id, days=365)
    days = {c.checkin_date for c in checkins}

    today = date.today()

    # Longest run anywhere in the history, not just the one ending today.
    longest = 0
    for day in days:
        if (day - timedelta(days=1)) in days:
            continue  # not the start of a run
        run = 0
        cursor = day
        while cursor in days:
            run += 1
            cursor += timedelta(days=1)
        longest = max(longest, run)

    if today in days:
        cursor = today
    elif (today - timedelta(days=1)) in days:
        cursor = today - timedelta(days=1)
    else:
        return APIResponse(
            success=True,
            data={
                "current_streak": 0,
                "longest_streak": longest,
                "checked_in_today": False,
            },
        )

    current = 0
    while cursor in days:
        current += 1
        cursor -= timedelta(days=1)

    return APIResponse(
        success=True,
        data={
            "current_streak": current,
            "longest_streak": longest,
            "checked_in_today": today in days,
        },
    )


@router.post(
    "",
    response_model=APIResponse[CheckInRead],
    summary="Record (or overwrite) a check-in",
)
async def create_checkin(
    data: CheckInCreate,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Record a check-in for a day, defaulting to today.

    Posting twice for the same day updates the existing entry, which is
    what re-rating your day should do.
    """
    checkin = await checkin_service.create_or_update(db, user.id, data)
    return APIResponse(success=True, data=_serialize(checkin))


@router.patch(
    "/{checkin_id}",
    response_model=APIResponse[CheckInRead],
    summary="Update a check-in",
)
async def update_checkin(
    checkin_id: UUID,
    data: CheckInUpdate,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Patch an existing check-in's scores or note."""
    checkin = await checkin_service.update(db, user.id, checkin_id, data)
    return APIResponse(success=True, data=_serialize(checkin))


@router.delete(
    "/{checkin_id}",
    response_model=APIResponse[dict],
    summary="Delete a check-in",
)
async def delete_checkin(
    checkin_id: UUID,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a check-in."""
    await checkin_service.delete(db, user.id, checkin_id)
    return APIResponse(success=True, data={"deleted": True}, message="Check-in deleted")
