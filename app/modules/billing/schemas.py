import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


# ==========================================
# Tax Schemas
# ==========================================
class TaxRuleCreate(BaseModel):
    name: str = Field(..., max_length=100)
    tax_rate: Decimal = Field(..., ge=Decimal("0.0000"), le=Decimal("1.0000"))
    tax_type: str = Field(default="GST", max_length=50)
    inclusive_or_exclusive: str = Field(default="EXCLUSIVE")  # EXCLUSIVE, INCLUSIVE
    effective_from: Optional[date] = None
    effective_until: Optional[date] = None
    active: bool = True


class TaxRuleUpdate(BaseModel):
    name: Optional[str] = None
    tax_rate: Optional[Decimal] = None
    tax_type: Optional[str] = None
    inclusive_or_exclusive: Optional[str] = None
    effective_from: Optional[date] = None
    effective_until: Optional[date] = None
    active: Optional[bool] = None


class TaxRuleResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    tax_rate: Decimal
    tax_type: str
    inclusive_or_exclusive: str
    effective_from: date
    effective_until: Optional[date] = None
    active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# Discount Schemas
# ==========================================
class DiscountCreate(BaseModel):
    discount_name: str = Field(..., max_length=100)
    discount_code: Optional[str] = None
    discount_type: str = Field(..., description="FIXED or PERCENTAGE")
    discount_value: Decimal = Field(..., ge=Decimal("0.00"))
    minimum_purchase: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"))
    minimum_quantity: int = Field(default=0, ge=0)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    usage_limit: Optional[int] = None
    product_id: Optional[uuid.UUID] = None
    subscription_wide: bool = True
    active: bool = True


class DiscountUpdate(BaseModel):
    discount_name: Optional[str] = None
    discount_code: Optional[str] = None
    discount_type: Optional[str] = None
    discount_value: Optional[Decimal] = None
    minimum_purchase: Optional[Decimal] = None
    minimum_quantity: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    usage_limit: Optional[int] = None
    product_id: Optional[uuid.UUID] = None
    subscription_wide: Optional[bool] = None
    active: Optional[bool] = None


class DiscountValidateRequest(BaseModel):
    purchase_subtotal: Decimal
    quantity: int = 1
    evaluation_date: Optional[date] = None


class DiscountResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    discount_name: str
    discount_code: Optional[str] = None
    discount_type: str
    discount_value: Decimal
    minimum_purchase: Decimal
    minimum_quantity: int
    start_date: date
    end_date: Optional[date] = None
    usage_limit: Optional[int] = None
    usage_count: int
    product_id: Optional[uuid.UUID] = None
    subscription_wide: bool
    active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# Invoice Schemas
# ==========================================
class InvoiceItemCreate(BaseModel):
    product_id: Optional[uuid.UUID] = None
    variant_id: Optional[uuid.UUID] = None
    description_snapshot: str
    quantity: int = Field(default=1, ge=1)
    unit_price: Decimal = Field(..., ge=Decimal("0.00"))


class InvoiceCreate(BaseModel):
    customer_id: uuid.UUID
    subscription_id: Optional[uuid.UUID] = None
    due_date: date
    billing_period_start: Optional[date] = None
    billing_period_end: Optional[date] = None
    currency: str = "INR"
    invoice_type: str = "ONE_TIME"
    discount_id: Optional[uuid.UUID] = None
    tax_rule_ids: Optional[List[uuid.UUID]] = None
    notes: Optional[str] = None
    items: List[InvoiceItemCreate]


class InvoiceItemResponse(BaseModel):
    id: uuid.UUID
    product_id: Optional[uuid.UUID] = None
    variant_id: Optional[uuid.UUID] = None
    description_snapshot: str
    quantity: int
    unit_price: Decimal
    discount_amount: Decimal
    tax_amount: Decimal
    line_total: Decimal

    model_config = ConfigDict(from_attributes=True)


class InvoiceResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    customer_id: uuid.UUID
    subscription_id: Optional[uuid.UUID] = None
    invoice_number: str
    issue_date: date
    due_date: date
    billing_period_start: Optional[date] = None
    billing_period_end: Optional[date] = None
    currency: str
    subtotal: Decimal
    discount_total: Decimal
    tax_total: Decimal
    total_amount: Decimal
    amount_paid: Decimal
    amount_due: Decimal
    status: str
    invoice_type: str
    verification_status: str
    notes: Optional[str] = None
    items: List[InvoiceItemResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InvoiceStatusUpdate(BaseModel):
    status: str


# ==========================================
# Recurring Billing Schemas
# ==========================================
class BillingRunCreate(BaseModel):
    as_of_date: Optional[date] = None


class BillingRunItemResponse(BaseModel):
    id: uuid.UUID
    subscription_id: uuid.UUID
    invoice_id: Optional[uuid.UUID] = None
    status: str
    error_message: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BillingRunResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    run_reference: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str
    total_processed: int
    successful_count: int
    failed_count: int
    logs: Optional[List[str]] = []
    created_at: datetime
    items: List[BillingRunItemResponse] = []

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# Payment Schemas
# ==========================================
class PaymentCreate(BaseModel):
    customer_id: Optional[uuid.UUID] = None
    invoice_id: Optional[uuid.UUID] = None
    amount: Decimal = Field(..., gt=Decimal("0.00"))
    payment_method: str = "BANK_TRANSFER"
    currency: str = "INR"
    reference: Optional[str] = None
    transaction_reference: Optional[str] = None
    notes: Optional[str] = None


class PaymentAllocateRequest(BaseModel):
    invoice_id: uuid.UUID
    amount: Decimal = Field(..., gt=Decimal("0.00"))
    notes: Optional[str] = None


class PaymentRefundRequest(BaseModel):
    amount: Decimal = Field(..., gt=Decimal("0.00"))
    reason: str


class PaymentAllocationResponse(BaseModel):
    id: uuid.UUID
    payment_id: uuid.UUID
    invoice_id: uuid.UUID
    amount_allocated: Decimal
    allocated_at: datetime
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PaymentResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    customer_id: Optional[uuid.UUID] = None
    invoice_id: Optional[uuid.UUID] = None
    payment_reference: str
    amount: Decimal
    currency: str
    payment_method: str
    payment_date: datetime
    transaction_reference: Optional[str] = None
    notes: Optional[str] = None
    status: str
    created_at: datetime
    allocations: List[PaymentAllocationResponse] = []

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# Reconciliation Schemas
# ==========================================
class ReconciliationReviewRequest(BaseModel):
    decision: str  # MATCH, REJECT
    matched_invoice_id: Optional[uuid.UUID] = None
    notes: Optional[str] = None


class ReconciliationItemResponse(BaseModel):
    id: uuid.UUID
    transaction_date: date
    reference: str
    description: str
    amount: Decimal
    currency: str
    matched_payment_id: Optional[uuid.UUID] = None
    matched_invoice_id: Optional[uuid.UUID] = None
    match_status: str
    confidence_score: Decimal
    review_notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ReconciliationRunResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    run_reference: str
    imported_at: datetime
    filename: str
    total_records: int
    matched_count: int
    unmatched_count: int
    discrepancy_count: int
    status: str
    items: List[ReconciliationItemResponse] = []

    model_config = ConfigDict(from_attributes=True)


class MatchTransactionRequest(BaseModel):
    transactionId: str
    invoiceId: str


# ==========================================
# Verification Schemas
# ==========================================
class ServiceCommitmentCreate(BaseModel):
    commitment_type: str
    expected_value: Decimal
    measurement_unit: str = "PERCENTAGE"
    verification_rule: str = "GREATER_OR_EQUAL"
    penalty_rate_per_unit: Decimal = Decimal("0.00")


class ContractCreate(BaseModel):
    subscription_id: uuid.UUID
    contract_reference: str
    start_date: date
    end_date: Optional[date] = None
    document_reference: Optional[str] = None
    commitments: List[ServiceCommitmentCreate] = []


class ServiceEventCreate(BaseModel):
    subscription_id: uuid.UUID
    commitment_id: Optional[uuid.UUID] = None
    event_type: str
    actual_value: Decimal
    event_timestamp: datetime
    evidence_reference: str
    source: str = "MONITORING_SYSTEM"
    status: str = "VERIFIED"


class ServiceCreditResponse(BaseModel):
    id: uuid.UUID
    subscription_id: uuid.UUID
    verification_result_id: uuid.UUID
    proposed_credit: Decimal
    approved_credit: Optional[Decimal] = None
    status: str
    approved_by: Optional[uuid.UUID] = None
    approval_reason: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VerificationResultResponse(BaseModel):
    id: uuid.UUID
    commitment_id: uuid.UUID
    expected_value: Decimal
    actual_value: Decimal
    variance: Decimal
    result: str
    explanation: str
    evidence_reference: Optional[str] = None
    service_credits: List[ServiceCreditResponse] = []

    model_config = ConfigDict(from_attributes=True)


class VerificationRunResponse(BaseModel):
    id: uuid.UUID
    subscription_id: uuid.UUID
    contract_id: uuid.UUID
    run_date: datetime
    status: str
    overall_result: str
    results: List[VerificationResultResponse] = []
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CreditApprovalRequest(BaseModel):
    approved_amount: Optional[Decimal] = None
    notes: Optional[str] = None
    reason: Optional[str] = None


# ==========================================
# AI Schemas
# ==========================================
class AnomalyResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    invoice_id: uuid.UUID
    anomaly_type: str
    severity: str
    detected_value: str
    expected_value: str
    explanation: str
    detection_method: str
    status: str
    reviewed_by: Optional[uuid.UUID] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AnomalyReviewRequest(BaseModel):
    decision: str = "RESOLVED"  # RESOLVED, FALSE_POSITIVE


class AssistantQueryRequest(BaseModel):
    prompt: Optional[str] = None
    query: Optional[str] = None


class AssistantQueryResponse(BaseModel):
    query: str
    category: str
    answer: str
    data: Any = None
    sources: List[str] = []


# ==========================================
# Audit Schemas
# ==========================================
class AuditEventResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    actor_id: Optional[uuid.UUID] = None
    action: str
    entity_type: str
    entity_id: uuid.UUID
    timestamp: datetime
    change_summary: str
    previous_hash: str
    current_hash: str
    is_anchored: bool
    blockchain_tx_hash: Optional[str] = None
    blockchain_network: Optional[str] = None
    anchored_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class AuditVerifyResponse(BaseModel):
    is_valid: bool
    total_blocks_checked: int = 0
    head_hash: Optional[str] = None
    verified_at: str
    details: Optional[str] = None
    tampered_block_index: Optional[int] = None
    tampered_block_id: Optional[str] = None
    expected_hash: Optional[str] = None
    actual_hash: Optional[str] = None
    expected_previous_hash: Optional[str] = None
    actual_previous_hash: Optional[str] = None


class AuditAnchorRequest(BaseModel):
    network: Optional[str] = "Ethereum Sepolia Testnet"


class AuditAnchorResponse(BaseModel):
    anchored: bool
    tx_hash: Optional[str] = None
    network: Optional[str] = None
    head_hash: Optional[str] = None
    anchored_at: Optional[str] = None
    message: Optional[str] = None
