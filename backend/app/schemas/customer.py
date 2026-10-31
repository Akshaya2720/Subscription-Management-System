"""Customer, customer address, and customer contact schemas."""

from datetime import datetime
from typing import Literal, Optional
import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class CustomerCreate(BaseModel):
    """Schema for creating a new customer."""

    customer_code: str = Field(..., min_length=1, max_length=50, description="Unique customer code within tenant")
    company_name: str = Field(..., min_length=1, max_length=255, description="Customer company or trading name")
    contact_name: Optional[str] = Field(default=None, max_length=255, description="Primary contact person name")
    email: Optional[EmailStr] = Field(default=None, description="Primary customer contact email")
    phone: Optional[str] = Field(default=None, max_length=50, description="Customer phone number")
    billing_address: Optional[str] = Field(default=None, description="Default billing address line")
    tax_identifier: Optional[str] = Field(default=None, max_length=100, description="VAT/GST or Tax ID")


class CustomerUpdate(BaseModel):
    """Schema for updating an existing customer."""

    company_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    contact_name: Optional[str] = Field(default=None, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, max_length=50)
    billing_address: Optional[str] = None
    tax_identifier: Optional[str] = Field(default=None, max_length=100)
    status: Optional[str] = Field(
        default=None,
        description="Customer status: active, inactive, or suspended",
    )

    @field_validator("status", mode="before")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        val = str(v).lower()
        if val not in {"active", "inactive", "suspended"}:
            raise ValueError("status must be one of: 'active', 'inactive', 'suspended'")
        return val


class CustomerAddressCreate(BaseModel):
    """Schema for creating a customer address."""

    address_type: str = Field(
        ...,
        description="Type of address: 'billing', 'shipping', or 'both'",
    )
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    is_default: bool = False

    @field_validator("address_type", mode="before")
    @classmethod
    def validate_address_type(cls, v: str) -> str:
        val = str(v).lower()
        if val not in {"billing", "shipping", "both"}:
            raise ValueError("address_type must be one of: 'billing', 'shipping', 'both'")
        return val


class CustomerAddressResponse(BaseModel):
    """Schema for returning customer address details."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    customer_id: uuid.UUID
    address_type: str
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    is_default: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None


class CustomerContactCreate(BaseModel):
    """Schema for creating a customer contact person."""

    full_name: str = Field(..., min_length=1, max_length=255, description="Contact person full name")
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, max_length=50)
    role: Optional[str] = Field(default=None, max_length=100)
    is_primary: bool = False


class CustomerContactResponse(BaseModel):
    """Schema for returning customer contact details."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    customer_id: uuid.UUID
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    is_primary: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None


class CustomerResponse(BaseModel):
    """Schema for customer representation."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    customer_code: str
    company_name: str
    contact_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    billing_address: Optional[str] = None
    tax_identifier: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None


class CustomerDetailResponse(CustomerResponse):
    """Schema for customer representation including nested addresses and contacts."""

    addresses: list[CustomerAddressResponse] = Field(default_factory=list)
    contacts: list[CustomerContactResponse] = Field(default_factory=list)
