"""
Insights router: correlations between mood and everything else.

Separate from /dashboard because the two answer different questions.
The dashboard says what happened; insights says what it appears to be
connected to.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.common import APIResponse
from app.schemas.insights import InsightsSummary
from app.services import insights_service

router = APIRouter(prefix="/insights", tags=["Insights"])


@router.get(
    "/summary",
    response_model=APIResponse[InsightsSummary],
    summary="Mood correlations across habits, weekdays, and tags",
)
async def get_insights(
    days: int = Query(30, ge=7, le=365, description="Size of the trailing window"),
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    How mood moves with the rest of the record.

    Four aggregations over the trailing window: mood on days a habit was
    kept versus missed, mood by day of week, the distribution of mood
    scores, and mood on days each tag was written about. `headline` is the
    strongest of those signals stated in a sentence, or null when nothing
    clears the noise floor.
    """
    summary = await insights_service.build_summary(db, user.id, days)
    return APIResponse(success=True, data=summary)
