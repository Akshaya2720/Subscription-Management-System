import uuid
from decimal import Decimal
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator


class BillingFrequencyEnum(str, Enum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    YEARLY = "YEARLY"


class PlanBase(BaseModel):
    name: str = Field(..., max_length=255, description="Plan name, e.g. Professional Monthly")
    description: Optional[str] = Field(None, description="Detailed plan description")
    billing_frequency: BillingFrequencyEnum = Field(..., description="Billing frequency: DAILY, WEEKLY, MONTHLY, YEARLY")
    plan_price: Decimal = Field(..., ge=Decimal("0.00"), description="Recurring plan price")
    minimum_quantity: int = Field(1, ge=1, description="Minimum quantity required to subscribe")
    start_availability_date: Optional[date] = Field(None, description="Date from which plan is available")
    end_availability_date: Optional[date] = Field(None, description="Date until which plan is available")
    auto_close_configuration: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Auto-close rules, e.g. max_failed_payments")
    early_closure_configuration: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Early closure policy and fees")
    pause_configuration: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Pause limit and grace days")
    renewal_configuration: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Renewal rules and notification days")
    status: str = Field("ACTIVE", description="Status: ACTIVE, ARCHIVED, DRAFT")

    @field_validator("plan_price", mode="before")
    @classmethod
    def validate_price(cls, v):
        if v is not None:
            return Decimal(str(v)).quantize(Decimal("0.01"))
        return Decimal("0.00")

    @model_validator(mode="after")
    def validate_dates(self):
        if self.start_availability_date and self.end_availability_date:
            if self.start_availability_date > self.end_availability_date:
                raise ValueError("start_availability_date cannot be later than end_availability_date")
        return self


class PlanCreate(PlanBase):
    pass


class PlanUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    billing_frequency: Optional[BillingFrequencyEnum] = None
    plan_price: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    minimum_quantity: Optional[int] = Field(None, ge=1)
    start_availability_date: Optional[date] = None
    end_availability_date: Optional[date] = None
    auto_close_configuration: Optional[Dict[str, Any]] = None
    early_closure_configuration: Optional[Dict[str, Any]] = None
    pause_configuration: Optional[Dict[str, Any]] = None
    renewal_configuration: Optional[Dict[str, Any]] = None
    status: Optional[str] = None

    @field_validator("plan_price", mode="before")
    @classmethod
    def validate_price(cls, v):
        if v is not None:
            return Decimal(str(v)).quantize(Decimal("0.01"))
        return None

    @model_validator(mode="after")
    def validate_dates(self):
        if self.start_availability_date and self.end_availability_date:
            if self.start_availability_date > self.end_availability_date:
                raise ValueError("start_availability_date cannot be later than end_availability_date")
        return self


class PlanPriceHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    plan_id: uuid.UUID
    price: Decimal
    effective_from: datetime
    notes: Optional[str] = None
    created_at: datetime


class PlanResponse(PlanBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    price_history: List[PlanPriceHistoryResponse] = []


class PlanPaginatedResponse(BaseModel):
    items: List[PlanResponse]
    total: int
    page: int
    per_page: int
    pages: int
