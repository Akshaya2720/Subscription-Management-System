import uuid
from decimal import Decimal
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict, field_validator


class QuotationItemCreate(BaseModel):
    product_id: uuid.UUID
    variant_id: Optional[uuid.UUID] = None
    plan_id: Optional[uuid.UUID] = None
    description: Optional[str] = None
    quantity: int = Field(1, ge=1)
    unit_price: Optional[Decimal] = Field(None, ge=Decimal("0.00"), description="Optional override; if omitted, snapshot from product/variant price")
    tax_configuration_reference: Optional[str] = Field(None, description="e.g. GST_18, VAT_20")

    @field_validator("unit_price", mode="before")
    @classmethod
    def validate_price(cls, v):
        if v is not None:
            return Decimal(str(v)).quantize(Decimal("0.01"))
        return None


class QuotationItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    quotation_id: uuid.UUID
    product_id: uuid.UUID
    variant_id: Optional[uuid.UUID] = None
    plan_id: Optional[uuid.UUID] = None
    description: str
    quantity: int
    unit_price: Decimal
    tax_configuration_reference: Optional[str] = None
    line_total: Decimal


class QuotationCreate(BaseModel):
    customer_id: uuid.UUID
    quotation_number: Optional[str] = Field(None, description="Auto-generated if not supplied")
    quotation_date: Optional[date] = Field(default_factory=date.today)
    expiry_date: date = Field(..., description="Date after which quotation is expired")
    discount_total: Optional[Decimal] = Field(Decimal("0.00"), ge=Decimal("0.00"))
    notes: Optional[str] = None
    items: List[QuotationItemCreate] = Field(..., min_length=1, description="List of quotation items")

    @field_validator("discount_total", mode="before")
    @classmethod
    def validate_discount(cls, v):
        if v is not None:
            return Decimal(str(v)).quantize(Decimal("0.01"))
        return Decimal("0.00")


class QuotationUpdate(BaseModel):
    expiry_date: Optional[date] = None
    discount_total: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    notes: Optional[str] = None
    items: Optional[List[QuotationItemCreate]] = None

    @field_validator("discount_total", mode="before")
    @classmethod
    def validate_discount(cls, v):
        if v is not None:
            return Decimal(str(v)).quantize(Decimal("0.01"))
        return None


class QuotationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    customer_id: uuid.UUID
    quotation_number: str
    quotation_date: date
    expiry_date: date
    status: str
    subtotal: Decimal
    discount_total: Decimal
    tax_total: Decimal
    grand_total: Decimal
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    items: List[QuotationItemResponse] = []


class QuotationPaginatedResponse(BaseModel):
    items: List[QuotationResponse]
    total: int
    page: int
    per_page: int
    pages: int


class ConvertToSubscriptionRequest(BaseModel):
    plan_id: Optional[uuid.UUID] = Field(None, description="Subscription plan ID; if omitted, checks quotation items or first available plan")
    start_date: Optional[date] = Field(default_factory=date.today, description="Subscription start date")
    billing_frequency: Optional[str] = Field(None, description="DAILY, WEEKLY, MONTHLY, YEARLY; defaults to plan frequency")
    payment_terms: str = Field("NET_30", description="Payment terms, e.g. NET_30, IMMEDIATE")
    currency: str = Field("INR", description="Currency symbol, e.g. INR, USD")
