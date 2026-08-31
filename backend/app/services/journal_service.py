"""
Journal service: entry CRUD, tag assignment, search and filtering.

Search uses a LIKE scan rather than the FULLTEXT index because MySQL's
natural-language mode ignores words shorter than ft_min_token_size (4 by
default) and drops very common words entirely -- surprising behaviour for
a personal journal where "sad" and "ok" are exactly what you search for.
The FULLTEXT index stays defined for relevance-ranked search later.
"""

from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError
from app.models.wellness import EntryTag, JournalEntry, Tag
from app.schemas.wellness import JournalCreate, JournalUpdate


def _base_query(user_id: UUID):
    """Entries for one user, with tags eagerly loaded to avoid N+1 queries."""
    return (
        select(JournalEntry)
        .where(JournalEntry.user_id == user_id)
        .options(selectinload(JournalEntry.tags))
    )


async def get_owned(
    db: AsyncSession,
    user_id: UUID,
    entry_id: UUID,
) -> JournalEntry:
    """
    Fetch an entry belonging to this user.

    Raises:
        NotFoundError: If it does not exist or belongs to someone else.
    """
    result = await db.execute(_base_query(user_id).where(JournalEntry.id == entry_id))
    entry = result.scalar_one_or_none()
    if not entry:
        raise NotFoundError("Journal entry not found")
    return entry


async def list_entries(
    db: AsyncSession,
    user_id: UUID,
    search: Optional[str] = None,
    tag_ids: Optional[Sequence[UUID]] = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[JournalEntry], int]:
    """
    List entries newest-first, optionally filtered by text and/or tags.

    When several tag_ids are given the filter is OR (entries carrying any
    of them), matching how the frontend tag chips behave.

    Returns:
        (entries for this page, total matching count)
    """
    query = _base_query(user_id)
    count_query = (
        select(func.count(func.distinct(JournalEntry.id)))
        .select_from(JournalEntry)
        .where(JournalEntry.user_id == user_id)
    )

    if search:
        pattern = f"%{search.strip()}%"
        condition = or_(
            JournalEntry.title.like(pattern),
            JournalEntry.content.like(pattern),
        )
        query = query.where(condition)
        count_query = count_query.where(condition)

    if tag_ids:
        subquery = (
            select(EntryTag.entry_id)
            .where(EntryTag.tag_id.in_(list(tag_ids)))
            .distinct()
        )
        query = query.where(JournalEntry.id.in_(subquery))
        count_query = count_query.where(JournalEntry.id.in_(subquery))

    total = (await db.execute(count_query)).scalar_one()

    query = (
        query.order_by(JournalEntry.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(query)
    return list(result.scalars().unique().all()), total


async def _resolve_tags(
    db: AsyncSession,
    user_id: UUID,
    tag_ids: Sequence[str],
) -> list[Tag]:
    """
    Turn a list of tag ids into the user's Tag rows.

    Ids that are malformed, unknown, or owned by another user are dropped
    rather than raising: a stale chip in the UI should not fail a save.
    """
    parsed: list[UUID] = []
    for raw in tag_ids:
        try:
            parsed.append(UUID(str(raw)))
        except (ValueError, TypeError):
            continue

    if not parsed:
        return []

    result = await db.execute(
        select(Tag).where(Tag.user_id == user_id, Tag.id.in_(parsed))
    )
    return list(result.scalars().all())


async def create(
    db: AsyncSession,
    user_id: UUID,
    data: JournalCreate,
) -> JournalEntry:
    """Create an entry and attach its tags."""
    entry = JournalEntry(
        user_id=user_id,
        title=data.title or "Untitled",
        content=data.content,
    )
    entry.tags = await _resolve_tags(db, user_id, data.tag_ids)

    db.add(entry)
    await db.flush()
    await db.refresh(entry, attribute_names=["tags"])
    return entry


async def update(
    db: AsyncSession,
    user_id: UUID,
    entry_id: UUID,
    data: JournalUpdate,
) -> JournalEntry:
    """
    Patch an entry. When tag_ids is present it replaces the whole tag set;
    when absent the existing tags are left alone.
    """
    entry = await get_owned(db, user_id, entry_id)
    update_dict = data.model_dump(exclude_unset=True)

    if "tag_ids" in update_dict:
        entry.tags = await _resolve_tags(db, user_id, update_dict.pop("tag_ids") or [])

    for field, value in update_dict.items():
        setattr(entry, field, value)

    await db.flush()
    await db.refresh(entry, attribute_names=["tags"])
    return entry


async def delete(db: AsyncSession, user_id: UUID, entry_id: UUID) -> None:
    """Delete an entry; its entry_tags rows go with it via ON DELETE CASCADE."""
    entry = await get_owned(db, user_id, entry_id)
    await db.delete(entry)
    await db.flush()
