"""Quotation Template and Quotation Models."""

import enum
import uuid
from datetime import date
from decimal import Decimal
from typing import Optional, List
from sqlalchemy import (
    String,
    Text,
    Numeric,
    Boolean,
    Date,
    ForeignKey,
    Uuid,
    Integer,
    UniqueConstraint,
    CheckConstraint,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class QuotationStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SENT = "SENT"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    CONVERTED = "CONVERTED"


class QuotationTemplate(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Reusable quotation template with preconfigured plan and product lines."""

    __tablename__ = "quotation_templates"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    plan_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("subscription_plans.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    default_valid_days: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    template_items: Mapped[List["QuotationTemplateItem"]] = relationship(
        "QuotationTemplateItem",
        back_populates="template",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("organization_id", "name", name="uq_org_quotation_template_name"),
        CheckConstraint("default_valid_days > 0", name="ck_template_valid_days_pos"),
    )


class QuotationTemplateItem(Base, UUIDPrimaryKeyMixin):
    """Preset product line inside a quotation template."""

    __tablename__ = "quotation_template_items"

    template_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("quotation_templates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
    )
    variant_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("product_variants.id", ondelete="SET NULL"),
        nullable=True,
    )
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    template: Mapped["QuotationTemplate"] = relationship("QuotationTemplate", back_populates="template_items")

    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_template_item_qty_pos"),
    )


class Quotation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Commercial proposal with locked pricing snapshots."""

    __tablename__ = "quotations"

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
    quotation_number: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    template_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("quotation_templates.id", ondelete="SET NULL"),
        nullable=True,
    )
    quotation_date: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    expiry_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(
        String(30),
        default="DRAFT",
        nullable=False,
        index=True,
    )
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    discount_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    tax_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    grand_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    customer = relationship("Customer", back_populates="quotations")
    subscription = relationship("Subscription", back_populates="quotation", uselist=False)
    items: Mapped[List["QuotationItem"]] = relationship(
        "QuotationItem",
        back_populates="quotation",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("organization_id", "quotation_number", name="uq_org_quotation_number"),
        CheckConstraint("subtotal >= 0", name="ck_quotation_subtotal_nonneg"),
        CheckConstraint("discount_total >= 0", name="ck_quotation_discount_nonneg"),
        CheckConstraint("tax_total >= 0", name="ck_quotation_tax_nonneg"),
        CheckConstraint("grand_total >= 0", name="ck_quotation_grand_total_nonneg"),
        Index("ix_quotations_org_status", "organization_id", "status"),
    )


class QuotationItem(Base, UUIDPrimaryKeyMixin):
    """Line item in quotation with locked unit prices."""

    __tablename__ = "quotation_items"

    quotation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("quotations.id", ondelete="CASCADE"),
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
        ForeignKey("product_variants.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    plan_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("subscription_plans.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    tax_configuration_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    line_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    quotation: Mapped["Quotation"] = relationship("Quotation", back_populates="items")
    product = relationship("Product")
    variant = relationship("ProductVariant")
    plan = relationship("SubscriptionPlan")

    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_quote_item_quantity_pos"),
        CheckConstraint("unit_price >= 0", name="ck_quote_item_unit_price_nonneg"),
        CheckConstraint("line_total >= 0", name="ck_quote_item_line_total_nonneg"),
    )
