"""
FastAPI application factory.

Creates and configures the FastAPI app with:
- Lifespan events (startup/shutdown)
- All middleware (CORS, logging, rate limiting, error handling)
- All routers under /api/v1/
- Auto-generated OpenAPI documentation
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import get_settings
from app.core.database import close_db, init_db
from app.core.middleware import setup_middleware
from app.routers import (
    ai,
    auth,
    checkins,
    dashboard,
    habits,
    health,
    insights,
    journal,
    tags,
    users,
)

settings = get_settings()

# Configure structured logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("sankalp")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events.

    Startup:
    - Initialize database tables (dev mode)

    Shutdown:
    - Close database connections
    """
    # === STARTUP ===
    logger.info(f"Starting {settings.app_name} ({settings.app_env})")

    # Initialize database
    try:
        await init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        logger.warning("App will start but database features may not work")

    logger.info(f"{settings.app_name} is ready")

    yield

    # === SHUTDOWN ===
    logger.info("Shutting down...")
    await close_db()
    logger.info("Shutdown complete")


def create_app() -> FastAPI:
    """
    Application factory.

    Creates a FastAPI instance with all configuration, middleware, and routes.
    """
    app = FastAPI(
        title=f"{settings.app_name} API",
        description=(
            "SanKalp wellness companion API. "
            "Provides authentication, daily check-ins, journalling with tags, "
            "habit tracking, dashboard analytics, and AI reflections."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # Register middleware
    setup_middleware(app)

    # Register routers under /api/v1/
    api_prefix = "/api/v1"
    app.include_router(health.router, prefix=api_prefix)
    app.include_router(auth.router, prefix=api_prefix)
    app.include_router(users.router, prefix=api_prefix)
    app.include_router(ai.router, prefix=api_prefix)
    app.include_router(checkins.router, prefix=api_prefix)
    app.include_router(journal.router, prefix=api_prefix)
    app.include_router(tags.router, prefix=api_prefix)
    app.include_router(habits.router, prefix=api_prefix)
    app.include_router(dashboard.router, prefix=api_prefix)
    app.include_router(insights.router, prefix=api_prefix)

    return app


# Create the app instance
app = create_app()
