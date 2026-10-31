"""Organization and organization settings schemas."""

from datetime import datetime
from typing import Any, Optional
import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class OrganizationCreate(BaseModel):
    """Schema for creating a new organization."""

    name: str = Field(..., min_length=2, max_length=255, description="Organization name")
    email: EmailStr = Field(..., description="Primary contact/billing email")
    phone: Optional[str] = Field(default=None, max_length=50, description="Contact phone number")
    address: Optional[str] = Field(default=None, description="Billing/physical address")
    industry: Optional[str] = Field(default=None, max_length=100, description="Industry sector")


class OrganizationUpdate(BaseModel):
    """Schema for updating an existing organization."""

    name: Optional[str] = Field(default=None, min_length=2, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=50)
    address: Optional[str] = Field(default=None)
    industry: Optional[str] = Field(default=None, max_length=100)


class OrganizationResponse(BaseModel):
    """Schema for organization response data."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None
    industry: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime


class OrganizationSettingsResponse(BaseModel):
    """Schema for organization settings response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    default_currency: str
    timezone: str
    tax_configuration: Optional[dict[str, Any]] = None
    billing_preferences: Optional[dict[str, Any]] = None


class OrganizationSettingsUpdate(BaseModel):
    """Schema for updating organization settings."""

    default_currency: Optional[str] = Field(default=None, min_length=3, max_length=3)
    timezone: Optional[str] = Field(default=None, max_length=50)
    tax_configuration: Optional[dict[str, Any]] = None
    billing_preferences: Optional[dict[str, Any]] = None
