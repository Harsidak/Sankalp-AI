"""
Schemas for whole-account operations: export and deletion.

The export is deliberately a plain nested structure rather than the paged,
enveloped shapes the rest of the API uses -- it is meant to be saved to a
file and read by a human, not consumed by the SPA.
"""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class ExportedCheckIn(BaseModel):
    checkin_date: date
    mood_score: int
    energy_score: int
    note: Optional[str] = None


class ExportedJournalEntry(BaseModel):
    title: str
    content: str
    tags: list[str] = []
    created_at: datetime
    updated_at: datetime


class ExportedHabit(BaseModel):
    name: str
    color: str
    target_per_week: int
    is_archived: bool
    completed_dates: list[date] = []


class ExportedTag(BaseModel):
    name: str
    color: str


class AccountExport(BaseModel):
    """Everything one account owns, in one document."""

    exported_at: datetime
    email: str
    full_name: Optional[str] = None
    member_since: datetime
    checkins: list[ExportedCheckIn] = []
    journal_entries: list[ExportedJournalEntry] = []
    habits: list[ExportedHabit] = []
    tags: list[ExportedTag] = []
    counts: dict[str, int] = Field(
        default_factory=dict,
        description="Row totals per table, so the export can be checked at a glance",
    )


class DeleteAccountRequest(BaseModel):
    """
    Confirmation for an irreversible delete.

    The password is required for password accounts; Google-only accounts
    have none to check, so they confirm with the literal phrase instead.
    """

    password: Optional[str] = Field(
        None, description="Current password. Required unless the account is OAuth-only."
    )
    confirm: str = Field(
        ...,
        description="Must be the exact string DELETE, so a stray request cannot do this",
    )


class DeleteAccountResult(BaseModel):
    """What the cascade actually removed."""

    deleted: bool = True
    removed: dict[str, int] = Field(
        default_factory=dict, description="Rows deleted per table, counted before the delete"
    )
