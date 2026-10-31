"""Pydantic schemas for Taxes, Discounts, Invoicing, Payments, and Automated Billing Runs."""

import uuid
from decimal import Decimal
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field

from app.models.billing import InvoiceStatus, PaymentMethod, DiscountType


# ── Tax Rules ─────────────────────────────────────────────────────────────

class TaxRuleBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    tax_code: str = Field(..., min_length=2, max_length=50)
    rate_percent: Decimal = Field(..., ge=Decimal("0.00"), le=Decimal("100.00"))
    country: Optional[str] = Field(None, max_length=100)
    state_province: Optional[str] = Field(None, max_length=100)
    is_default: bool = False
    is_active: bool = True
    description: Optional[str] = None


class TaxRuleCreate(TaxRuleBase):
    pass


class TaxRuleUpdate(BaseModel):
    name: Optional[str] = None
    rate_percent: Optional[Decimal] = Field(None, ge=Decimal("0.00"), le=Decimal("100.00"))
    country: Optional[str] = None
    state_province: Optional[str] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None
    description: Optional[str] = None


class TaxRuleResponse(TaxRuleBase):
    id: uuid.UUID
    organization_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Discounts ─────────────────────────────────────────────────────────────

class DiscountBase(BaseModel):
    code: str = Field(..., min_length=2, max_length=50)
    description: Optional[str] = None
    discount_type: DiscountType = DiscountType.PERCENTAGE
    amount: Decimal = Field(..., ge=Decimal("0.00"))
    min_purchase_amount: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"))
    min_quantity: int = Field(default=1, ge=1)
    max_uses: Optional[int] = Field(None, ge=1)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    product_id: Optional[uuid.UUID] = None
    plan_id: Optional[uuid.UUID] = None
    is_active: bool = True


class DiscountCreate(DiscountBase):
    pass


class DiscountUpdate(BaseModel):
    description: Optional[str] = None
    amount: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    min_purchase_amount: Optional[Decimal] = None
    min_quantity: Optional[int] = None
    max_uses: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: Optional[bool] = None


class DiscountResponse(DiscountBase):
    id: uuid.UUID
    organization_id: uuid.UUID
    times_used: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Invoices ──────────────────────────────────────────────────────────────

class InvoiceItemBase(BaseModel):
    product_id: Optional[uuid.UUID] = None
    description: str
    quantity: int = Field(..., ge=1)
    unit_price: Decimal = Field(..., ge=Decimal("0.00"))
    tax_percent: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"))
    discount_amount: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"))


class InvoiceItemCreate(InvoiceItemBase):
    pass


class InvoiceItemResponse(InvoiceItemBase):
    id: uuid.UUID
    invoice_id: uuid.UUID
    tax_amount: Decimal = Decimal("0.00")
    line_total: Decimal

    model_config = {"from_attributes": True}


class InvoiceBase(BaseModel):
    customer_id: uuid.UUID
    subscription_id: Optional[uuid.UUID] = None
    issue_date: date = Field(default_factory=date.today)
    due_date: date
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    currency: str = "USD"
    notes: Optional[str] = None


class InvoiceCreate(InvoiceBase):
    items: List[InvoiceItemCreate]
    discount_code: Optional[str] = None


class InvoiceUpdate(BaseModel):
    due_date: Optional[date] = None
    notes: Optional[str] = None


class InvoiceResponse(InvoiceBase):
    id: uuid.UUID
    organization_id: uuid.UUID
    invoice_number: str
    status: InvoiceStatus
    subtotal: Decimal
    discount_amount: Decimal
    tax_amount: Decimal
    sla_credit_amount: Decimal
    total_amount: Decimal
    amount_paid: Decimal
    amount_due: Decimal
    items: List[InvoiceItemResponse] = []
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ── Payments ──────────────────────────────────────────────────────────────

class PaymentCreate(BaseModel):
    amount: Decimal = Field(..., gt=Decimal("0.00"))
    payment_method: PaymentMethod = PaymentMethod.SIMULATED
    reference: Optional[str] = None
    notes: Optional[str] = None


class PaymentResponse(BaseModel):
    id: uuid.UUID
    invoice_id: uuid.UUID
    amount: Decimal
    payment_method: PaymentMethod
    payment_date: datetime
    status: str
    reference: Optional[str] = None
    notes: Optional[str] = None
    gateway_transaction_id: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class PaymentReceipt(BaseModel):
    receipt_id: str
    payment_id: uuid.UUID
    invoice_id: uuid.UUID
    invoice_number: str
    amount_paid: Decimal
    remaining_balance: Decimal
    payment_method: str
    timestamp: datetime
    status: str
    message: str


# ── Billing Run ───────────────────────────────────────────────────────────

class BillingRunRequest(BaseModel):
    run_date: date = Field(default_factory=date.today)
    auto_confirm: bool = True


class BillingRunResponse(BaseModel):
    run_date: date
    subscriptions_scanned: int
    invoices_created: int
    invoices_skipped: int
    total_billed_amount: Decimal
    created_invoice_ids: List[uuid.UUID]
