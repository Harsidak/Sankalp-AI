"""
Habit router: habit CRUD and per-day completion toggling.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.common import APIResponse
from app.schemas.wellness import (
    HabitCreate,
    HabitLogResult,
    HabitLogToggle,
    HabitRead,
    HabitUpdate,
)
from app.services import habit_service

router = APIRouter(prefix="/habits", tags=["Habits"])


def _serialize(habit) -> HabitRead:
    """Combine stored columns with the derived streak fields."""
    derived = habit_service.summarize(habit)
    return HabitRead(
        id=str(habit.id),
        name=habit.name,
        icon=habit.icon,
        color=habit.color,
        target_per_week=habit.target_per_week,
        is_archived=habit.is_archived,
        created_at=habit.created_at,
        **derived,
    )


@router.get(
    "",
    response_model=APIResponse[list[HabitRead]],
    summary="List habits with streaks",
)
async def list_habits(
    include_archived: bool = Query(False),
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List habits, each with its completed dates and computed streaks.

    The completed dates ship with the habit so the calendar heatmap can
    render without a second round trip per habit.
    """
    habits = await habit_service.list_habits(db, user.id, include_archived)
    return APIResponse(success=True, data=[_serialize(h) for h in habits])


@router.get(
    "/{habit_id}",
    response_model=APIResponse[HabitRead],
    summary="Get one habit",
)
async def get_habit(
    habit_id: UUID,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Fetch a single habit with its logs and streaks."""
    habit = await habit_service.get_owned(db, user.id, habit_id)
    return APIResponse(success=True, data=_serialize(habit))


@router.post(
    "",
    response_model=APIResponse[HabitRead],
    status_code=201,
    summary="Create a habit",
)
async def create_habit(
    data: HabitCreate,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a habit to track."""
    habit = await habit_service.create(db, user.id, data)
    return APIResponse(success=True, data=_serialize(habit))


@router.patch(
    "/{habit_id}",
    response_model=APIResponse[HabitRead],
    summary="Update or archive a habit",
)
async def update_habit(
    habit_id: UUID,
    data: HabitUpdate,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a habit's details, or set is_archived to retire it while
    keeping its history.
    """
    habit = await habit_service.update(db, user.id, habit_id, data)
    return APIResponse(success=True, data=_serialize(habit))


@router.delete(
    "/{habit_id}",
    response_model=APIResponse[dict],
    summary="Delete a habit permanently",
)
async def delete_habit(
    habit_id: UUID,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Permanently delete a habit and every log it has. Archiving is usually
    the better choice, since it preserves the record.
    """
    await habit_service.delete(db, user.id, habit_id)
    return APIResponse(success=True, data={"deleted": True}, message="Habit deleted")


@router.post(
    "/{habit_id}/log",
    response_model=APIResponse[HabitLogResult],
    summary="Toggle a habit's completion for a day",
)
async def toggle_log(
    habit_id: UUID,
    data: HabitLogToggle,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Mark a habit done for a day, or undo it if it was already marked.

    One endpoint handles both directions so the UI checkbox has a single
    call to make, and the response carries the recomputed streaks.
    """
    habit, day, completed = await habit_service.toggle_log(
        db, user.id, habit_id, data.completed_date
    )
    derived = habit_service.summarize(habit)

    return APIResponse(
        success=True,
        data=HabitLogResult(
            habit_id=str(habit.id),
            completed_date=day,
            completed=completed,
            current_streak=derived["current_streak"],
            longest_streak=derived["longest_streak"],
        ),
    )
