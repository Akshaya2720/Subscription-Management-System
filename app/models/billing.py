"""Billing, Tax Rules, Discounts, Invoices, and Payments Models."""

import enum
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional, List
from sqlalchemy import (
    String,
    Text,
    Numeric,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Uuid,
    Integer,
    UniqueConstraint,
    CheckConstraint,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, synonym

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class DiscountType(str, enum.Enum):
    PERCENTAGE = "PERCENTAGE"
    FIXED_AMOUNT = "FIXED_AMOUNT"


class PaymentMethod(str, enum.Enum):
    BANK_TRANSFER = "BANK_TRANSFER"
    CREDIT_CARD = "CREDIT_CARD"
    CRYPTO = "CRYPTO"
    SIMULATED = "SIMULATED"
    MANUAL = "MANUAL"


class InvoiceStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    ISSUED = "ISSUED"
    CONFIRMED = "CONFIRMED"
    PARTIALLY_PAID = "PARTIALLY_PAID"
    PAID = "PAID"
    OVERDUE = "OVERDUE"
    CANCELLED = "CANCELLED"


class PaymentStatus(str, enum.Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class TaxRule(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Admin-configured tax rules applied during billing and quotations."""

    __tablename__ = "tax_rules"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    tax_type: Mapped[str] = mapped_column(String(50), default="VAT", nullable=False)
    rate_percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    country_code: Mapped[str] = mapped_column(String(10), default="US", nullable=False)
    state_or_province: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    tax_code = synonym("tax_type")
    rate_percent = synonym("rate_percentage")
    country = synonym("country_code")
    state_province = synonym("state_or_province")

    __table_args__ = (
        UniqueConstraint("organization_id", "name", name="uq_org_tax_rule_name"),
        CheckConstraint(
            "rate_percentage >= 0 AND rate_percentage <= 100",
            name="ck_tax_rate_percent_range",
        ),
        Index("ix_tax_rules_org_active", "organization_id", "is_active"),
    )


class Discount(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Admin-configured promotional discount coupons with usage tracking."""

    __tablename__ = "discounts"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    discount_type: Mapped[str] = mapped_column(String(20), default="PERCENTAGE", nullable=False)
    discount_value: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    min_purchase_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    min_quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    max_uses: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    times_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    product_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    applies_to_subscription: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    description = synonym("name")
    amount = synonym("discount_value")

    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_org_discount_code"),
        CheckConstraint("discount_value >= 0", name="ck_discount_value_nonneg"),
        CheckConstraint("min_purchase_amount >= 0", name="ck_discount_min_purchase_nonneg"),
        CheckConstraint("min_quantity >= 1", name="ck_discount_min_qty_pos"),
        CheckConstraint("times_used >= 0", name="ck_discount_times_used_nonneg"),
        CheckConstraint("max_uses IS NULL OR max_uses > 0", name="ck_discount_max_uses_pos"),
        CheckConstraint("end_date IS NULL OR end_date >= start_date", name="ck_discount_date_order"),
        Index("ix_discounts_org_code_active", "organization_id", "code", "is_active"),
    )


class Invoice(Base, UUIDPrimaryKeyMixin):
    """Itemized billing invoice generated from subscription intervals."""

    __tablename__ = "invoices"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    subscription_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("subscriptions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    invoice_number: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    issue_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    due_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    period_start: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    period_end: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)

    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    discount_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    sla_credit_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    tax_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    amount_paid: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    amount_due: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    discount_amount = synonym("discount_total")
    tax_amount = synonym("tax_total")

    status: Mapped[str] = mapped_column(String(30), default="ISSUED", nullable=False, index=True)
    verification_status: Mapped[str] = mapped_column(String(30), default="VERIFIED", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    subscription = relationship("Subscription", back_populates="invoices")
    items: Mapped[List["InvoiceItem"]] = relationship(
        "InvoiceItem",
        back_populates="invoice",
        cascade="all, delete-orphan",
    )
    status_history: Mapped[List["InvoiceStatusHistory"]] = relationship(
        "InvoiceStatusHistory",
        back_populates="invoice",
        cascade="all, delete-orphan",
    )
    payments: Mapped[List["Payment"]] = relationship(
        "Payment",
        back_populates="invoice",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("organization_id", "invoice_number", name="uq_org_invoice_number"),
        # PREVENTS DOUBLE BILLING FOR SAME SUBSCRIPTION PERIOD
        UniqueConstraint("subscription_id", "period_start", "period_end", name="uq_invoice_subscription_period"),
        CheckConstraint("period_end IS NULL OR period_start IS NULL OR period_end >= period_start", name="ck_invoice_period_order"),
        CheckConstraint("due_date >= issue_date", name="ck_invoice_due_date_order"),
        CheckConstraint("subtotal >= 0", name="ck_invoice_subtotal_nonneg"),
        CheckConstraint("discount_total >= 0", name="ck_invoice_discount_nonneg"),
        CheckConstraint("sla_credit_amount >= 0", name="ck_invoice_sla_credit_nonneg"),
        CheckConstraint("tax_total >= 0", name="ck_invoice_tax_nonneg"),
        CheckConstraint("total_amount >= 0", name="ck_invoice_total_nonneg"),
        CheckConstraint("amount_paid >= 0", name="ck_invoice_paid_nonneg"),
        CheckConstraint("amount_due >= 0", name="ck_invoice_due_nonneg"),
        Index("ix_invoices_org_status_due", "organization_id", "status", "due_date"),
    )


class InvoiceItem(Base, UUIDPrimaryKeyMixin):
    """Line item on an invoice."""

    __tablename__ = "invoice_items"

    invoice_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    line_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="items")

    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_inv_item_qty_pos"),
        CheckConstraint("unit_price >= 0", name="ck_inv_item_unit_price_nonneg"),
        CheckConstraint("line_total >= 0", name="ck_inv_item_line_total_nonneg"),
    )


class InvoiceStatusHistory(Base, UUIDPrimaryKeyMixin):
    """Audit log of status transitions for invoices."""

    __tablename__ = "invoice_status_history"

    invoice_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    from_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    to_status: Mapped[str] = mapped_column(String(50), nullable=False)
    changed_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="status_history")


class Payment(Base, UUIDPrimaryKeyMixin):
    """Settlement transaction recorded against an invoice."""

    __tablename__ = "payments"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    payment_method: Mapped[str] = mapped_column(String(50), default="BANK_TRANSFER", nullable=False)
    payment_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    transaction_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="COMPLETED", nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="payments")

    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_payment_amount_pos"),
        Index("ix_payments_invoice_status", "invoice_id", "status"),
    )
