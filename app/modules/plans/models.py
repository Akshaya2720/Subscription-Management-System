import uuid
from decimal import Decimal
from datetime import datetime, date, timezone
from sqlalchemy import String, Text, Numeric, Date, DateTime, JSON, ForeignKey, Uuid, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"
    __table_args__ = (
        UniqueConstraint("organization_id", "name", name="uq_org_plan_name"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    billing_frequency: Mapped[str] = mapped_column(String(20), nullable=False)  # DAILY, WEEKLY, MONTHLY, YEARLY
    plan_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    minimum_quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    start_availability_date: Mapped[date] = mapped_column(Date, nullable=True)
    end_availability_date: Mapped[date] = mapped_column(Date, nullable=True)
    auto_close_configuration: Mapped[dict] = mapped_column(JSON, default=dict, nullable=True)
    early_closure_configuration: Mapped[dict] = mapped_column(JSON, default=dict, nullable=True)
    pause_configuration: Mapped[dict] = mapped_column(JSON, default=dict, nullable=True)
    renewal_configuration: Mapped[dict] = mapped_column(JSON, default=dict, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="ACTIVE", nullable=False, index=True)  # ACTIVE, ARCHIVED, DRAFT
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    price_history = relationship("PlanPriceHistory", back_populates="plan", cascade="all, delete-orphan", order_by="PlanPriceHistory.created_at.desc()")
    subscriptions = relationship("Subscription", back_populates="plan")


class PlanPriceHistory(Base):
    __tablename__ = "plan_price_history"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("subscription_plans.id", ondelete="CASCADE"), nullable=False, index=True
    )
    price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    notes: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    plan = relationship("SubscriptionPlan", back_populates="price_history")
