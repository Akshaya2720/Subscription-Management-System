"""Common Pydantic schemas for API responses and pagination."""

from datetime import datetime
from typing import Generic, Optional, TypeVar
import uuid

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class MessageResponse(BaseModel):
    """Standard message response."""

    model_config = ConfigDict(from_attributes=True)

    message: str
    detail: Optional[str] = None


class PaginatedResponse(BaseModel, Generic[T]):
    """Standard paginated response wrapper."""

    model_config = ConfigDict(from_attributes=True)

    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int
