"""
Async SQLAlchemy database engine and session management.

Uses the aiomysql driver for async MySQL access. Provides a session
factory and a FastAPI dependency for scoped sessions.
"""

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

settings = get_settings()

# Connection pooling options apply to real server-backed databases.
# SQLite (used by the test suite) is served by StaticPool, which rejects
# these arguments outright, so they are only passed when relevant.
_engine_kwargs: dict = {"echo": settings.debug}
if not settings.database_url.startswith("sqlite"):
    _engine_kwargs.update(
        pool_size=5,
        max_overflow=10,
        pool_recycle=3600,  # Recycle connections after 1 hour
        pool_pre_ping=True,  # Verify connections before use
    )

engine = create_async_engine(settings.database_url, **_engine_kwargs)

# Session factory — produces scoped async sessions
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Keep objects usable after commit
)


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy ORM models.
    All models inherit from this to share metadata and common behavior.
    """
    pass


async def get_db():
    """
    FastAPI dependency that yields an async database session.
    Automatically commits on success, rolls back on exception,
    and closes the session when the request is done.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """
    Create all tables (for development/hackathon use).
    In production, use Alembic migrations instead.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Dispose the engine and close all connections."""
    await engine.dispose()
