import uuid
from datetime import datetime, date, timezone
from decimal import Decimal
from typing import Optional, List
from sqlalchemy import (
    String,
    Text,
    Numeric,
    Date,
    DateTime,
    Boolean,
    JSON,
    ForeignKey,
    Uuid,
    Integer,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Invoice(Base):
    __tablename__ = "invoices"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "subscription_id",
            "billing_period_start",
            "billing_period_end",
            "invoice_type",
            name="uq_invoice_sub_period_type",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    subscription_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("subscriptions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    invoice_number: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    issue_date: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    billing_period_start: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    billing_period_end: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    currency: Mapped[str] = mapped_column(String(10), default="INR", nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    discount_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    tax_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    amount_paid: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    amount_due: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    status: Mapped[str] = mapped_column(String(30), default="DRAFT", nullable=False)  # DRAFT, CONFIRMED, PARTIALLY_PAID, PAID, OVERDUE, CANCELLED, VOIDED
    invoice_type: Mapped[str] = mapped_column(String(30), default="RECURRING", nullable=False)  # RECURRING, ONE_TIME, CREDIT_NOTE, ADJUSTMENT
    verification_status: Mapped[str] = mapped_column(String(30), default="VERIFIED", nullable=False)  # VERIFIED, PENDING, FLAGGED
    pdf_path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    customer = relationship("Customer")
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="invoice", cascade="all, delete-orphan")
    allocations = relationship("PaymentAllocation", back_populates="invoice", cascade="all, delete-orphan")

    @property
    def invoice_date(self) -> date:
        return self.issue_date

    @invoice_date.setter
    def invoice_date(self, value: date):
        self.issue_date = value

    @property
    def grand_total(self) -> Decimal:
        return self.total_amount

    @grand_total.setter
    def grand_total(self, value: Decimal):
        self.total_amount = value


class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True
    )
    variant_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("product_variants.id", ondelete="SET NULL"), nullable=True, index=True
    )
    description_snapshot: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"), nullable=False)
    line_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    invoice = relationship("Invoice", back_populates="items")
    product = relationship("Product")
    variant = relationship("ProductVariant")


class BillingRun(Base):
    __tablename__ = "billing_runs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    run_reference: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="PENDING", nullable=False)  # PENDING, RUNNING, COMPLETED, FAILED, COMPLETED_WITH_ERRORS
    total_processed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    successful_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    logs: Mapped[list] = mapped_column(JSON, default=list, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    items = relationship("BillingRunItem", back_populates="billing_run", cascade="all, delete-orphan")


class BillingRunItem(Base):
    __tablename__ = "billing_run_items"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    billing_run_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("billing_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    subscription_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("subscriptions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    invoice_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("invoices.id", ondelete="SET NULL"), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False)  # SUCCESS, FAILED, SKIPPED
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    billing_run = relationship("BillingRun", back_populates="items")
    subscription = relationship("Subscription")
    invoice = relationship("Invoice")


class TaxRule(Base):
    __tablename__ = "tax_rules"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    tax_rate: Mapped[Decimal] = mapped_column(Numeric(6, 4), nullable=False)  # e.g. 0.1800 for 18%
    tax_type: Mapped[str] = mapped_column(String(50), default="GST", nullable=False)
    inclusive_or_exclusive: Mapped[str] = mapped_column(String(20), default="EXCLUSIVE", nullable=False)  # EXCLUSIVE, INCLUSIVE
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_until: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class Discount(Base):
    __tablename__ = "discounts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    discount_name: Mapped[str] = mapped_column(String(100), nullable=False)
    discount_code: Mapped[Optional[str]] = mapped_column(String(50), index=True, nullable=True)
    discount_type: Mapped[str] = mapped_column(String(20), nullable=False)  # FIXED, PERCENTAGE
    discount_value: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    minimum_purchase: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"), nullable=False)
    minimum_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    usage_limit: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    product_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("products.id", ondelete="SET NULL"), nullable=True
    )
    subscription_wide: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    redemptions = relationship("DiscountRedemption", back_populates="discount", cascade="all, delete-orphan")


class DiscountRedemption(Base):
    __tablename__ = "discount_redemptions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    discount_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("discounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    amount_applied: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    redeemed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    discount = relationship("Discount", back_populates="redemptions")
    invoice = relationship("Invoice")
    customer = relationship("Customer")


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    customer_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=True, index=True
    )
    invoice_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("invoices.id", ondelete="SET NULL"), nullable=True, index=True
    )
    payment_reference: Mapped[str] = mapped_column(
        String(100), default=lambda: f"PAY-{uuid.uuid4().hex[:8].upper()}", nullable=False, index=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="INR", nullable=False)
    payment_method: Mapped[str] = mapped_column(String(50), default="BANK_TRANSFER", nullable=False)
    payment_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    transaction_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="COMPLETED", nullable=False)  # COMPLETED, PENDING, FAILED, REFUNDED, PARTIALLY_REFUNDED
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    invoice = relationship("Invoice", back_populates="payments")
    customer = relationship("Customer")
    allocations = relationship("PaymentAllocation", back_populates="payment", cascade="all, delete-orphan")
    refunds = relationship("PaymentRefund", back_populates="payment", cascade="all, delete-orphan")


class PaymentAllocation(Base):
    __tablename__ = "payment_allocations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    payment_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("payments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True
    )
    amount_allocated: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    allocated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    payment = relationship("Payment", back_populates="allocations")
    invoice = relationship("Invoice", back_populates="allocations")


class PaymentRefund(Base):
    __tablename__ = "payment_refunds"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    payment_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("payments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    refund_reference: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    refund_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="COMPLETED", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    payment = relationship("Payment", back_populates="refunds")


class ReconciliationRun(Base):
    __tablename__ = "reconciliation_runs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    run_reference: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    imported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    total_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    matched_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    unmatched_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    discrepancy_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="PENDING_REVIEW", nullable=False)

    items = relationship("ReconciliationItem", back_populates="reconciliation_run", cascade="all, delete-orphan")


class ReconciliationItem(Base):
    __tablename__ = "reconciliation_items"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reconciliation_run_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("reconciliation_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    transaction_date: Mapped[date] = mapped_column(Date, nullable=False)
    reference: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="INR", nullable=False)
    matched_payment_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("payments.id", ondelete="SET NULL"), nullable=True
    )
    matched_invoice_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("invoices.id", ondelete="SET NULL"), nullable=True
    )
    match_status: Mapped[str] = mapped_column(String(40), default="UNMATCHED", nullable=False)
    confidence_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0.00"), nullable=False)
    review_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reviewed_by: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    reconciliation_run = relationship("ReconciliationRun", back_populates="items")
    payment = relationship("Payment")
    invoice = relationship("Invoice")


class Contract(Base):
    __tablename__ = "contracts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    subscription_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("subscriptions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    contract_reference: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    document_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="ACTIVE", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    subscription = relationship("Subscription")
    commitments = relationship("ServiceCommitment", back_populates="contract", cascade="all, delete-orphan")


class ServiceCommitment(Base):
    __tablename__ = "service_commitments"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    commitment_type: Mapped[str] = mapped_column(String(50), nullable=False)  # UPTIME, RESPONSE_TIME, DELIVERED_HOURS, API_CALLS
    expected_value: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    measurement_unit: Mapped[str] = mapped_column(String(30), nullable=False)  # PERCENTAGE, HOURS, MILLISECONDS, COUNT
    verification_rule: Mapped[str] = mapped_column(String(30), default="GREATER_OR_EQUAL", nullable=False)
    penalty_rate_per_unit: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"), nullable=False)

    contract = relationship("Contract", back_populates="commitments")


class ServiceEvent(Base):
    __tablename__ = "service_events"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subscription_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("subscriptions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    commitment_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("service_commitments.id", ondelete="SET NULL"), nullable=True, index=True
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    actual_value: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    event_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    evidence_reference: Mapped[str] = mapped_column(String(255), nullable=False)
    source: Mapped[str] = mapped_column(String(50), default="MONITORING_SYSTEM", nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="VERIFIED", nullable=False)  # VERIFIED, UNVERIFIED, DISPUTED
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    subscription = relationship("Subscription")
    commitment = relationship("ServiceCommitment")


class VerificationRun(Base):
    __tablename__ = "verification_runs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subscription_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("subscriptions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    contract_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    run_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="COMPLETED", nullable=False)
    overall_result: Mapped[str] = mapped_column(String(30), nullable=False)  # COMPLIANT, BREACH, PARTIAL_BREACH
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    subscription = relationship("Subscription")
    contract = relationship("Contract")
    results = relationship("VerificationResult", back_populates="verification_run", cascade="all, delete-orphan")


class VerificationResult(Base):
    __tablename__ = "verification_results"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    verification_run_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("verification_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    commitment_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("service_commitments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    expected_value: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    actual_value: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    variance: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    result: Mapped[str] = mapped_column(String(20), nullable=False)  # PASS, FAIL, WARNING
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    verification_run = relationship("VerificationRun", back_populates="results")
    commitment = relationship("ServiceCommitment")
    service_credits = relationship("ServiceCredit", back_populates="verification_result", cascade="all, delete-orphan")


class ServiceCredit(Base):
    __tablename__ = "service_credits"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subscription_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("subscriptions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    verification_result_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("verification_results.id", ondelete="CASCADE"), nullable=False, index=True
    )
    proposed_credit: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    approved_credit: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="PROPOSED", nullable=False)  # PROPOSED, APPROVED, REJECTED, APPLIED
    approved_by: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), nullable=True)
    approval_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    applied_invoice_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("invoices.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    subscription = relationship("Subscription")
    verification_result = relationship("VerificationResult", back_populates="service_credits")
    invoice = relationship("Invoice")


class InvoiceAnomaly(Base):
    __tablename__ = "invoice_anomalies"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True
    )
    anomaly_type: Mapped[str] = mapped_column(String(60), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), default="MEDIUM", nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    detected_value: Mapped[str] = mapped_column(String(255), nullable=False)
    expected_value: Mapped[str] = mapped_column(String(255), nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    detection_method: Mapped[str] = mapped_column(String(50), default="RULE_BASED", nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="DETECTED", nullable=False)
    reviewed_by: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    invoice = relationship("Invoice")


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    actor_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    change_summary: Mapped[str] = mapped_column(Text, nullable=False)
    previous_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    current_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    is_anchored: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    blockchain_tx_hash: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    blockchain_network: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    anchored_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    actor = relationship("User")
