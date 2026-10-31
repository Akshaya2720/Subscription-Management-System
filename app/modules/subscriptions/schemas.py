import uuid
from decimal import Decimal
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator


class SubscriptionItemCreate(BaseModel):
    product_id: uuid.UUID
    variant_id: Optional[uuid.UUID] = None
    description_snapshot: Optional[str] = None
    quantity: int = Field(1, ge=1)
    unit_price_snapshot: Optional[Decimal] = Field(None, ge=Decimal("0.00"))

    @field_validator("unit_price_snapshot", mode="before")
    @classmethod
    def validate_price(cls, v):
        if v is not None:
            return Decimal(str(v)).quantize(Decimal("0.01"))
        return None


class SubscriptionItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    subscription_id: uuid.UUID
    product_id: uuid.UUID
    variant_id: Optional[uuid.UUID] = None
    description_snapshot: str
    quantity: int
    unit_price_snapshot: Decimal
    line_total: Decimal


class SubscriptionCreate(BaseModel):
    customer_id: uuid.UUID
    plan_id: uuid.UUID
    quotation_id: Optional[uuid.UUID] = None
    subscription_number: Optional[str] = None
    start_date: Optional[date] = Field(default_factory=date.today)
    billing_frequency: Optional[str] = Field(None, description="DAILY, WEEKLY, MONTHLY, YEARLY; defaults to plan frequency")
    payment_terms: str = Field("NET_30")
    currency: str = Field("INR")
    renewal_enabled: bool = True
    items: List[SubscriptionItemCreate] = Field(..., min_length=1)


class SubscriptionUpdate(BaseModel):
    payment_terms: Optional[str] = None
    renewal_enabled: Optional[bool] = None
    next_billing_date: Optional[date] = None
    expiry_date: Optional[date] = None


class SubscriptionPauseRequest(BaseModel):
    reason: str = Field(..., min_length=3, description="Reason for pausing subscription")
    resume_date: Optional[date] = Field(None, description="Expected resume date")


class SubscriptionResumeRequest(BaseModel):
    notes: Optional[str] = Field(None, description="Notes on resume")


class SubscriptionRenewRequest(BaseModel):
    extension_periods: int = Field(1, ge=1, description="Number of billing periods to extend")
    notes: Optional[str] = Field(None, description="Notes on renewal")


class SubscriptionCloseRequest(BaseModel):
    reason: str = Field(..., min_length=3, description="Reason for subscription closure")
    early_closure_fee: Optional[Decimal] = Field(None, ge=Decimal("0.00"), description="Early cancellation/termination penalty fee")

    @field_validator("early_closure_fee", mode="before")
    @classmethod
    def validate_fee(cls, v):
        if v is not None:
            return Decimal(str(v)).quantize(Decimal("0.01"))
        return None


class SubscriptionEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    subscription_id: uuid.UUID
    event_type: str
    previous_status: Optional[str] = None
    new_status: Optional[str] = None
    description: str
    metadata_json: Optional[Dict[str, Any]] = None
    created_at: datetime


class SubscriptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    customer_id: uuid.UUID
    plan_id: uuid.UUID
    quotation_id: Optional[uuid.UUID] = None
    subscription_number: str
    start_date: date
    next_billing_date: date
    expiry_date: Optional[date] = None
    billing_frequency: str
    payment_terms: str
    status: str
    currency: str
    renewal_enabled: bool
    pause_information: Optional[Dict[str, Any]] = None
    closure_information: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    items: List[SubscriptionItemResponse] = []


class SubscriptionPaginatedResponse(BaseModel):
    items: List[SubscriptionResponse]
    total: int
    page: int
    per_page: int
    pages: int


# --- Digital Twin Models ---

class DigitalTwinCustomer(BaseModel):
    id: uuid.UUID
    customer_code: str
    company_name: Optional[str] = None
    contact_name: str
    email: str
    phone: Optional[str] = None
    billing_address: Optional[str] = None
    tax_identifier: Optional[str] = None
    status: str


class DigitalTwinPlan(BaseModel):
    id: uuid.UUID
    name: str
    billing_frequency: str
    current_catalog_price: Decimal
    is_available: bool


class DigitalTwinInvoice(BaseModel):
    id: uuid.UUID
    invoice_number: str
    issue_date: date
    due_date: date
    subtotal: Decimal
    discount_total: Decimal
    tax_total: Decimal
    total_amount: Decimal
    status: str
    verification_status: str


class DigitalTwinPayment(BaseModel):
    id: uuid.UUID
    invoice_id: uuid.UUID
    amount: Decimal
    payment_method: str
    payment_date: datetime
    transaction_reference: Optional[str] = None
    status: str


class DigitalTwinQuotation(BaseModel):
    id: uuid.UUID
    quotation_number: str
    quotation_date: date
    expiry_date: date
    subtotal: Decimal
    discount_total: Decimal
    tax_total: Decimal
    grand_total: Decimal
    status: str


class DigitalTwinResponse(BaseModel):
    subscription_id: uuid.UUID
    subscription_number: str
    status: str
    start_date: date
    next_billing_date: date
    expiry_date: Optional[date] = None
    billing_frequency: str
    payment_terms: str
    currency: str
    renewal_enabled: bool
    contractual_recurring_price: Decimal
    total_contract_value: Decimal
    pause_information: Optional[Dict[str, Any]] = None
    closure_information: Optional[Dict[str, Any]] = None
    customer: DigitalTwinCustomer
    plan: DigitalTwinPlan
    subscription_items: List[SubscriptionItemResponse]
    quotations: List[DigitalTwinQuotation] = []
    invoices: List[DigitalTwinInvoice] = []
    payments: List[DigitalTwinPayment] = []
    subscription_change_history: List[SubscriptionEventResponse] = []
    verification_status: str


# --- Change Impact Models ---

class ProductImpactRequest(BaseModel):
    product_id: uuid.UUID
    proposed_sales_price: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    proposed_status: Optional[str] = Field(None, description="Proposed status, e.g. INACTIVE, ARCHIVED")

    @field_validator("proposed_sales_price", mode="before")
    @classmethod
    def validate_price(cls, v):
        if v is not None:
            return Decimal(str(v)).quantize(Decimal("0.01"))
        return None


class AffectedSubscriptionInfo(BaseModel):
    subscription_id: uuid.UUID
    subscription_number: str
    customer_id: uuid.UUID
    contracted_unit_price: Decimal
    proposed_unit_price: Optional[Decimal] = None
    status: str
    retains_contract_price: bool = True


class AffectedQuotationInfo(BaseModel):
    quotation_id: uuid.UUID
    quotation_number: str
    status: str
    current_snapshot_price: Decimal
    proposed_price: Optional[Decimal] = None


class ProductImpactResponse(BaseModel):
    product_id: uuid.UUID
    product_name: str
    current_sales_price: Decimal
    proposed_sales_price: Optional[Decimal] = None
    current_status: str
    proposed_status: Optional[str] = None
    active_subscriptions_count: int
    contractual_monthly_revenue_protected: Decimal
    affected_active_subscriptions: List[AffectedSubscriptionInfo]
    pending_quotations_count: int
    affected_quotations: List[AffectedQuotationInfo]
    business_policy_notice: str


class PlanImpactRequest(BaseModel):
    plan_id: uuid.UUID
    proposed_plan_price: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    proposed_status: Optional[str] = None
    proposed_billing_frequency: Optional[str] = None

    @field_validator("proposed_plan_price", mode="before")
    @classmethod
    def validate_price(cls, v):
        if v is not None:
            return Decimal(str(v)).quantize(Decimal("0.01"))
        return None


class PlanImpactResponse(BaseModel):
    plan_id: uuid.UUID
    plan_name: str
    current_plan_price: Decimal
    proposed_plan_price: Optional[Decimal] = None
    current_status: str
    proposed_status: Optional[str] = None
    active_subscriptions_count: int
    contractual_revenue_protected: Decimal
    affected_active_subscriptions: List[AffectedSubscriptionInfo]
    pending_quotations_count: int
    affected_quotations: List[AffectedQuotationInfo]
    business_policy_notice: str
