"""Authentication and profile schemas."""

from datetime import datetime
from typing import Optional
import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterRequest(BaseModel):
    """Schema for tenant/admin initial registration."""

    organization_name: str = Field(..., min_length=2, max_length=255, description="Tenant organization name")
    organization_email: EmailStr = Field(..., description="Organization billing/primary email")
    organization_phone: Optional[str] = Field(default=None, max_length=50, description="Organization contact phone")
    organization_industry: Optional[str] = Field(default=None, max_length=100, description="Organization industry")
    admin_full_name: str = Field(..., min_length=2, max_length=255, description="Initial admin full name")
    admin_email: EmailStr = Field(..., description="Initial admin user email")
    admin_password: str = Field(..., min_length=9, description="Admin password (at least 9 characters)")


class LoginRequest(BaseModel):
    """Schema for user credentials authentication."""

    email: EmailStr
    password: str
    organization_id: Optional[uuid.UUID] = Field(
        default=None,
        description="Optional organization ID if user belongs to multiple organizations",
    )


class TokenResponse(BaseModel):
    """JWT bearer token response schema."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    """Token refresh payload schema."""

    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    """Password reset request schema."""

    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    """Password reset response schema."""

    message: str
    reset_token: Optional[str] = Field(
        default=None,
        description="Password reset token (only populated in development mode when SMTP is not configured)",
    )


class ResetPasswordRequest(BaseModel):
    """Password reset confirmation schema."""

    token: str
    new_password: str = Field(..., min_length=9, description="New password (minimum 9 characters)")


class ChangePasswordRequest(BaseModel):
    """Authenticated user change password schema."""

    current_password: str
    new_password: str = Field(..., min_length=9, description="New password (minimum 9 characters)")


class OrganizationMembershipInfo(BaseModel):
    """Summary of organization membership and roles for a user profile."""

    model_config = ConfigDict(from_attributes=True)

    organization_id: uuid.UUID
    organization_name: str
    roles: list[str] = Field(default_factory=list)
    status: str


class UserProfileResponse(BaseModel):
    """Detailed profile response for the authenticated user."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    full_name: str
    email: str
    is_active: bool
    email_verified: bool
    created_at: datetime
    updated_at: datetime
    organizations: list[OrganizationMembershipInfo] = Field(default_factory=list)


class UpdateProfileRequest(BaseModel):
    """Request to update the current user's personal profile."""

    full_name: Optional[str] = Field(default=None, min_length=2, max_length=255)
