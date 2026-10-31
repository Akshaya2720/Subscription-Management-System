"""Product, Variant, and Subscription Plan Models."""

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


class BillingFrequency(str, enum.Enum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    YEARLY = "YEARLY"


class ProductStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ARCHIVED = "ARCHIVED"


class PlanStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ARCHIVED = "ARCHIVED"


class Product(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Software product or service definition."""

    __tablename__ = "products"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    product_type: Mapped[str] = mapped_column(String(50), default="SAAS", nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sales_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    cost_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="ACTIVE", nullable=False, index=True)

    variants: Mapped[List["ProductVariant"]] = relationship(
        "ProductVariant",
        back_populates="product",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("organization_id", "name", name="uq_org_product_name"),
        CheckConstraint("sales_price >= 0", name="ck_product_sales_price_nonneg"),
        Index("ix_products_org_status", "organization_id", "status"),
    )


class ProductVariant(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Product variant (e.g., brand additions, premium tier addons)."""

    __tablename__ = "product_variants"

    product_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    variant_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    additional_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="ACTIVE", nullable=False)

    product: Mapped["Product"] = relationship("Product", back_populates="variants")

    __table_args__ = (
        UniqueConstraint("product_id", "variant_name", name="uq_product_variant_name"),
        CheckConstraint("additional_price >= 0", name="ck_variant_price_nonneg"),
    )


class SubscriptionPlan(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Recurring subscription plan template."""

    __tablename__ = "subscription_plans"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    billing_frequency: Mapped[str] = mapped_column(String(20), default="MONTHLY", nullable=False)
    plan_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    minimum_quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    start_availability_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    end_availability_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # First-class PDF flags
    is_auto_close_at_end: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_closable_early: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_pausable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_renewable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Policy JSON configurations
    auto_close_configuration: Mapped[Optional[dict]] = mapped_column(JSON, default=dict, nullable=True)
    early_closure_configuration: Mapped[Optional[dict]] = mapped_column(JSON, default=dict, nullable=True)
    pause_configuration: Mapped[Optional[dict]] = mapped_column(JSON, default=dict, nullable=True)
    renewal_configuration: Mapped[Optional[dict]] = mapped_column(JSON, default=dict, nullable=True)

    status: Mapped[str] = mapped_column(String(30), default="ACTIVE", nullable=False, index=True)

    price_history: Mapped[List["PlanPriceHistory"]] = relationship(
        "PlanPriceHistory",
        back_populates="plan",
        cascade="all, delete-orphan",
        order_by="PlanPriceHistory.created_at.desc()",
    )
    subscriptions = relationship("Subscription", back_populates="plan")

    __table_args__ = (
        UniqueConstraint("organization_id", "name", name="uq_org_plan_name"),
        CheckConstraint("plan_price >= 0", name="ck_plan_price_nonneg"),
        CheckConstraint("minimum_quantity >= 1", name="ck_plan_min_qty"),
        CheckConstraint(
            "end_availability_date IS NULL OR start_availability_date IS NULL OR end_availability_date >= start_availability_date",
            name="ck_plan_availability_date_order",
        ),
        Index("ix_plans_org_status", "organization_id", "status"),
    )


class PlanPriceHistory(Base, UUIDPrimaryKeyMixin):
    """Historical audit ledger for plan price revisions."""

    __tablename__ = "plan_price_history"

    plan_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("subscription_plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    effective_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    notes: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    plan: Mapped["SubscriptionPlan"] = relationship("SubscriptionPlan", back_populates="price_history")
