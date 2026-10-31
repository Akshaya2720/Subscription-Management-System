"""User management schemas."""

from datetime import datetime
from typing import Literal, Optional
import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserResponse(BaseModel):
    """Schema for returning user details."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    full_name: str
    email: str
    is_active: bool
    email_verified: bool
    created_at: datetime
    updated_at: datetime
    roles: list[str] = Field(default_factory=list)


class CreateStaffRequest(BaseModel):
    """Schema for organization admins to invite or create staff members."""

    full_name: str = Field(..., min_length=2, max_length=255, description="Staff member full name")
    email: EmailStr = Field(..., description="Staff member email address")
    password: str = Field(..., min_length=9, description="Temporary or initial password (minimum 9 characters)")
    role: Literal["STAFF"] = Field(
        default="STAFF",
        description="Role assigned to the new user (limited to STAFF for this endpoint)",
    )


class UpdateUserRequest(BaseModel):
    """Schema for updating user attributes."""

    full_name: Optional[str] = Field(default=None, min_length=2, max_length=255)
    is_active: Optional[bool] = None
