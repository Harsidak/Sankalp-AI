"""
Tag router: user-scoped labels for journal entries.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.common import APIResponse
from app.schemas.wellness import TagCreate, TagRead, TagUpdate, TagWithCount
from app.services import tag_service

router = APIRouter(prefix="/tags", tags=["Tags"])


def _serialize(tag) -> TagRead:
    return TagRead(id=str(tag.id), name=tag.name, color=tag.color)


@router.get(
    "",
    response_model=APIResponse[list[TagWithCount]],
    summary="List tags with entry counts",
)
async def list_tags(
    with_counts: bool = Query(True, description="Include how many entries use each tag"),
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List the user's tags.

    With counts they are ordered most-used first; without, alphabetically.
    """
    if with_counts:
        rows = await tag_service.list_with_counts(db, user.id)
        data = [
            TagWithCount(
                id=str(tag.id),
                name=tag.name,
                color=tag.color,
                entry_count=count,
            )
            for tag, count in rows
        ]
    else:
        tags = await tag_service.list_all(db, user.id)
        data = [
            TagWithCount(id=str(t.id), name=t.name, color=t.color, entry_count=0)
            for t in tags
        ]

    return APIResponse(success=True, data=data)


@router.post(
    "",
    response_model=APIResponse[TagRead],
    status_code=201,
    summary="Create a tag",
)
async def create_tag(
    data: TagCreate,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a tag. Names are lowercased and must be unique per user."""
    tag = await tag_service.create(db, user.id, data)
    return APIResponse(success=True, data=_serialize(tag))


@router.patch(
    "/{tag_id}",
    response_model=APIResponse[TagRead],
    summary="Rename or recolour a tag",
)
async def update_tag(
    tag_id: UUID,
    data: TagUpdate,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a tag's name or colour."""
    tag = await tag_service.update(db, user.id, tag_id, data)
    return APIResponse(success=True, data=_serialize(tag))


@router.delete(
    "/{tag_id}",
    response_model=APIResponse[dict],
    summary="Delete a tag",
)
async def delete_tag(
    tag_id: UUID,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a tag. Entries carrying it are kept and simply lose the label,
    because the cascade runs across entry_tags, not journal_entries.
    """
    await tag_service.delete(db, user.id, tag_id)
    return APIResponse(success=True, data={"deleted": True}, message="Tag deleted")
