import uuid
from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class CustomerBase(BaseModel):
    customer_code: str = Field(..., max_length=50, description="Unique code for customer, e.g. CUST-001")
    company_name: Optional[str] = Field(None, max_length=255, description="Company/Business name")
    contact_name: str = Field(..., max_length=255, description="Primary contact person")
    email: EmailStr = Field(..., description="Customer billing/contact email")
    phone: Optional[str] = Field(None, max_length=50, description="Phone number")
    billing_address: Optional[str] = Field(None, max_length=500, description="Full billing address")
    tax_identifier: Optional[str] = Field(None, max_length=100, description="Tax ID / GSTIN / VAT number")
    status: str = Field("ACTIVE", description="Customer status: ACTIVE, INACTIVE, SUSPENDED")


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    customer_code: Optional[str] = Field(None, max_length=50)
    company_name: Optional[str] = Field(None, max_length=255)
    contact_name: Optional[str] = Field(None, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    billing_address: Optional[str] = Field(None, max_length=500)
    tax_identifier: Optional[str] = Field(None, max_length=100)
    status: Optional[str] = None


class CustomerResponse(CustomerBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class CustomerPaginatedResponse(BaseModel):
    items: List[CustomerResponse]
    total: int
    page: int
    per_page: int
    pages: int
