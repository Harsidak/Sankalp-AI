"""
Tag service: user-scoped labels for journal entries.

Tag names are unique per user (uq_tags_user_name), so the service checks
for a collision before insert and reports it as a ConflictError rather
than letting a raw IntegrityError reach the client.
"""

from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ConflictError, NotFoundError
from app.models.wellness import EntryTag, JournalEntry, Tag
from app.schemas.wellness import TagCreate, TagUpdate


async def get_owned(db: AsyncSession, user_id: UUID, tag_id: UUID) -> Tag:
    """
    Fetch a tag that belongs to this user.

    Raises:
        NotFoundError: If it does not exist or belongs to someone else.
    """
    result = await db.execute(
        select(Tag).where(Tag.id == tag_id, Tag.user_id == user_id)
    )
    tag = result.scalar_one_or_none()
    if not tag:
        raise NotFoundError("Tag not found")
    return tag


async def get_by_name(
    db: AsyncSession,
    user_id: UUID,
    name: str,
) -> Optional[Tag]:
    """Fetch one of the user's tags by name."""
    result = await db.execute(
        select(Tag).where(Tag.user_id == user_id, Tag.name == name)
    )
    return result.scalar_one_or_none()


async def list_all(db: AsyncSession, user_id: UUID) -> list[Tag]:
    """List the user's tags alphabetically."""
    result = await db.execute(
        select(Tag).where(Tag.user_id == user_id).order_by(Tag.name.asc())
    )
    return list(result.scalars().all())


async def list_with_counts(db: AsyncSession, user_id: UUID) -> list[tuple[Tag, int]]:
    """
    List tags alongside how many entries carry each one.

    A LEFT OUTER JOIN onto the join table keeps tags with zero entries in
    the result, which an inner join would silently drop.
    """
    stmt = (
        select(Tag, func.count(EntryTag.entry_id).label("entry_count"))
        .outerjoin(EntryTag, EntryTag.tag_id == Tag.id)
        .where(Tag.user_id == user_id)
        .group_by(Tag.id)
        .order_by(func.count(EntryTag.entry_id).desc(), Tag.name.asc())
    )
    result = await db.execute(stmt)
    return [(row[0], row[1]) for row in result.all()]


async def create(db: AsyncSession, user_id: UUID, data: TagCreate) -> Tag:
    """
    Create a tag.

    Raises:
        ConflictError: If the user already has a tag with this name.
    """
    if await get_by_name(db, user_id, data.name):
        raise ConflictError(f"You already have a tag named '{data.name}'")

    tag = Tag(user_id=user_id, name=data.name, color=data.color)
    db.add(tag)
    await db.flush()
    await db.refresh(tag)
    return tag


async def get_or_create(db: AsyncSession, user_id: UUID, name: str) -> Tag:
    """Fetch a tag by name, creating it if the user does not have it yet."""
    normalized = name.strip().lower()
    existing = await get_by_name(db, user_id, normalized)
    if existing:
        return existing

    tag = Tag(user_id=user_id, name=normalized)
    db.add(tag)
    await db.flush()
    await db.refresh(tag)
    return tag


async def update(
    db: AsyncSession,
    user_id: UUID,
    tag_id: UUID,
    data: TagUpdate,
) -> Tag:
    """
    Rename or recolour a tag.

    Raises:
        NotFoundError: If the tag is not the user's.
        ConflictError: If renaming would collide with another of their tags.
    """
    tag = await get_owned(db, user_id, tag_id)
    update_dict = data.model_dump(exclude_unset=True)

    new_name = update_dict.get("name")
    if new_name and new_name != tag.name:
        clash = await get_by_name(db, user_id, new_name)
        if clash:
            raise ConflictError(f"You already have a tag named '{new_name}'")

    for field, value in update_dict.items():
        setattr(tag, field, value)

    await db.flush()
    await db.refresh(tag)
    return tag


async def delete(db: AsyncSession, user_id: UUID, tag_id: UUID) -> None:
    """
    Delete a tag. Journal entries survive and simply lose the label.

    The tag's entries are eagerly loaded so the label can be detached from
    each one before the tag row goes. Deleting the tag alone would remove
    the entry_tags rows in the database, but any entry already loaded in
    this session would keep showing the tag until the session is discarded
    -- a re-query does not overwrite a collection the identity map holds.
    """
    result = await db.execute(
        select(Tag)
        .where(Tag.id == tag_id, Tag.user_id == user_id)
        .options(selectinload(Tag.entries).selectinload(JournalEntry.tags))
    )
    tag = result.scalar_one_or_none()
    if not tag:
        raise NotFoundError("Tag not found")

    for entry in list(tag.entries):
        if tag in entry.tags:
            entry.tags.remove(tag)

    await db.delete(tag)
    await db.flush()
