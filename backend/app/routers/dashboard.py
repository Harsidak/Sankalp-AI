"""
Dashboard router: the aggregated analytics payload.

One endpoint returns everything the dashboard renders, so the page makes
a single request instead of five and cannot show a half-loaded mix of
different time ranges.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.common import APIResponse
from app.schemas.wellness import DashboardSummary
from app.services import dashboard_service

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get(
    "/summary",
    response_model=APIResponse[DashboardSummary],
    summary="Aggregated dashboard analytics",
)
async def get_summary(
    days: int = Query(30, ge=7, le=365, description="Size of the trailing window"),
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Mood trend, averages, top tags, and habit completion counts for the
    trailing window ending today.

    Days with no check-in appear in mood_trend with null scores, so the
    chart can break the line rather than interpolate across a gap.
    """
    summary = await dashboard_service.build_summary(db, user.id, days)
    return APIResponse(success=True, data=summary)
