"""
Common Pydantic schemas used across all API endpoints.

Provides consistent response wrapping, pagination, and error formatting.
"""

from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorDetail(BaseModel):
    """Standardized error detail in API responses."""
    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Any] = Field(None, description="Additional error context")


class APIResponse(BaseModel, Generic[T]):
    """
    Uniform API response wrapper.
    Every endpoint returns this structure for consistency.
    """
    success: bool = True
    data: Optional[T] = None
    error: Optional[ErrorDetail] = None
    message: Optional[str] = None


class PaginationParams(BaseModel):
    """Query parameters for paginated list endpoints."""
    page: int = Field(1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class PaginatedResponse(BaseModel, Generic[T]):
    """Response wrapper for paginated list endpoints."""
    success: bool = True
    data: list[T] = []
    total: int = 0
    page: int = 1
    page_size: int = 20
    total_pages: int = 0


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    version: str = "1.0.0"
    database: str = "connected"
