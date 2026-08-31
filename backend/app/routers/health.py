"""
Health check router.

Verifies the API is running and the database is reachable.
"""

import logging

from fastapi import APIRouter
from sqlalchemy import text

from app.core.database import engine
from app.schemas.common import HealthResponse

router = APIRouter(tags=["Health"])
logger = logging.getLogger("sankalp")


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Verify the API and its database connection are operational.",
)
async def health_check():
    """Check API and database health."""
    db_status = "connected"

    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as e:
        logger.warning(f"Database health check failed: {e}")
        db_status = "disconnected"

    return HealthResponse(
        status="healthy" if db_status == "connected" else "degraded",
        database=db_status,
    )
