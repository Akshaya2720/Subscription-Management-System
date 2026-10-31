"""Subscription and Lifecycle Models."""

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
    JSON,
    ForeignKey,
    Uuid,
    Integer,
    UniqueConstraint,
    CheckConstraint,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class SubscriptionStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    QUOTATION = "QUOTATION"
    CONFIRMED = "CONFIRMED"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    CLOSED = "CLOSED"


class Subscription(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Core recurring subscription contract."""

    __tablename__ = "subscriptions"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("customers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    plan_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("subscription_plans.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    quotation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("quotations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    subscription_number: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    next_billing_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    expiry_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    billing_frequency: Mapped[str] = mapped_column(String(20), default="MONTHLY", nullable=False)
    payment_terms: Mapped[str] = mapped_column(String(50), default="NET_30", nullable=False)
    status: Mapped[str] = mapped_column(
        String(30),
        default="DRAFT",
        nullable=False,
        index=True,
    )
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    renewal_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    pause_information: Mapped[Optional[dict]] = mapped_column(JSON, default=dict, nullable=True)
    closure_information: Mapped[Optional[dict]] = mapped_column(JSON, default=dict, nullable=True)
    recurring_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)

    # Relationships
    customer = relationship("Customer", back_populates="subscriptions")
    plan = relationship("SubscriptionPlan", back_populates="subscriptions")
    quotation = relationship("Quotation", back_populates="subscription")
    items: Mapped[List["SubscriptionItem"]] = relationship(
        "SubscriptionItem",
        back_populates="subscription",
        cascade="all, delete-orphan",
    )
    events: Mapped[List["SubscriptionEvent"]] = relationship(
        "SubscriptionEvent",
        back_populates="subscription",
        cascade="all, delete-orphan",
        order_by="SubscriptionEvent.created_at.desc()",
    )
    invoices = relationship("Invoice", back_populates="subscription")

    __table_args__ = (
        UniqueConstraint("organization_id", "subscription_number", name="uq_org_subscription_number"),
        CheckConstraint("expiry_date IS NULL OR expiry_date >= start_date", name="ck_sub_date_order"),
        CheckConstraint("recurring_amount >= 0", name="ck_sub_recurring_amt_nonneg"),
        Index("ix_subscriptions_org_status", "organization_id", "status"),
        Index("ix_subscriptions_billing_due", "organization_id", "next_billing_date", "status"),
    )


class SubscriptionItem(Base, UUIDPrimaryKeyMixin):
    """Frozen contractual line item with price snapshot."""

    __tablename__ = "subscription_items"

    subscription_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("subscriptions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    variant_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("product_variants.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    description_snapshot: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    unit_price_snapshot: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    line_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    subscription: Mapped["Subscription"] = relationship("Subscription", back_populates="items")
    product = relationship("Product")
    variant = relationship("ProductVariant")

    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_sub_item_qty_pos"),
        CheckConstraint("unit_price_snapshot >= 0", name="ck_sub_item_unit_price_nonneg"),
        CheckConstraint("line_total >= 0", name="ck_sub_item_line_total_nonneg"),
    )


class SubscriptionEvent(Base, UUIDPrimaryKeyMixin):
    """Immutable transition audit record for subscription lifecycle."""

    __tablename__ = "subscription_events"

    subscription_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("subscriptions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    previous_status: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    new_status: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, default=dict, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    subscription: Mapped["Subscription"] = relationship("Subscription", back_populates="events")
