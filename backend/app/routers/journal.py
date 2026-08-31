"""
Journal router: entry CRUD plus search, tag filtering, and pagination.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.common import APIResponse, PaginatedResponse
from app.schemas.wellness import (
    JournalCreate,
    JournalRead,
    JournalUpdate,
    TagRead,
)
from app.services import journal_service

router = APIRouter(prefix="/journal", tags=["Journal"])


def _serialize(entry) -> JournalRead:
    return JournalRead(
        id=str(entry.id),
        title=entry.title,
        content=entry.content,
        tags=[
            TagRead(id=str(t.id), name=t.name, color=t.color)
            for t in entry.tags
        ],
        created_at=entry.created_at,
        updated_at=entry.updated_at,
    )


@router.get(
    "",
    response_model=PaginatedResponse[JournalRead],
    summary="List, search, and filter journal entries",
)
async def list_entries(
    search: Optional[str] = Query(None, description="Match against title and content"),
    tag_ids: Optional[list[UUID]] = Query(
        None,
        description="Repeatable. Entries carrying ANY of these tags match.",
    ),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List the user's entries newest-first.

    Search and tag filters compose: passing both narrows to entries that
    match the text AND carry at least one of the tags.
    """
    offset = (page - 1) * page_size
    entries, total = await journal_service.list_entries(
        db,
        user.id,
        search=search,
        tag_ids=tag_ids,
        limit=page_size,
        offset=offset,
    )

    return PaginatedResponse(
        success=True,
        data=[_serialize(e) for e in entries],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get(
    "/{entry_id}",
    response_model=APIResponse[JournalRead],
    summary="Get one journal entry",
)
async def get_entry(
    entry_id: UUID,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Fetch a single entry with its tags."""
    entry = await journal_service.get_owned(db, user.id, entry_id)
    return APIResponse(success=True, data=_serialize(entry))


@router.post(
    "",
    response_model=APIResponse[JournalRead],
    status_code=201,
    summary="Create a journal entry",
)
async def create_entry(
    data: JournalCreate,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Create an entry and attach any tags given by id."""
    entry = await journal_service.create(db, user.id, data)
    return APIResponse(success=True, data=_serialize(entry))


@router.put(
    "/{entry_id}",
    response_model=APIResponse[JournalRead],
    summary="Update a journal entry",
)
async def update_entry(
    entry_id: UUID,
    data: JournalUpdate,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Patch an entry. Sending tag_ids replaces the entry's whole tag set;
    omitting it leaves the existing tags untouched.
    """
    entry = await journal_service.update(db, user.id, entry_id, data)
    return APIResponse(success=True, data=_serialize(entry))


@router.delete(
    "/{entry_id}",
    response_model=APIResponse[dict],
    summary="Delete a journal entry",
)
async def delete_entry(
    entry_id: UUID,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete an entry. Its tag links go with it; the tags themselves stay."""
    await journal_service.delete(db, user.id, entry_id)
    return APIResponse(success=True, data={"deleted": True}, message="Entry deleted")
