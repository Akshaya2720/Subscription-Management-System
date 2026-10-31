"""Contract-to-Bill SLA Verification & SHA-256 Audit Trail Models."""

import enum
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from sqlalchemy import (
    String,
    Text,
    Numeric,
    Boolean,
    DateTime,
    ForeignKey,
    Uuid,
    Integer,
    UniqueConstraint,
    CheckConstraint,
    Index,
    Enum as SQLEnum,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class VerificationStatus(str, enum.Enum):
    PENDING_REVIEW = "PENDING_REVIEW"
    VERIFIED_COMPLIANT = "VERIFIED_COMPLIANT"
    CREDIT_APPROVED = "CREDIT_APPROVED"
    CREDIT_REJECTED = "CREDIT_REJECTED"


class VerificationContract(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """SLA contract telemetry verification comparing contractual uptime vs recorded delivery."""

    __tablename__ = "verification_contracts"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    contract_number: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    subscription_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("subscriptions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    service_name: Mapped[str] = mapped_column(String(255), nullable=False)
    sla_commitment_description: Mapped[str] = mapped_column(String(255), nullable=False)
    target_uptime_percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("99.99"), nullable=False)
    actual_recorded_telemetry: Mapped[str] = mapped_column(String(255), nullable=False)
    breach_detected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    proposed_credit_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    status: Mapped[VerificationStatus] = mapped_column(
        SQLEnum(VerificationStatus, native_enum=False, length=30),
        default=VerificationStatus.PENDING_REVIEW,
        nullable=False,
        index=True,
    )
    adjudicated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    adjudicated_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    __table_args__ = (
        UniqueConstraint("organization_id", "contract_number", name="uq_org_contract_number"),
        CheckConstraint(
            "target_uptime_percentage >= 0 AND target_uptime_percentage <= 100",
            name="ck_verification_uptime_range",
        ),
        CheckConstraint("proposed_credit_amount >= 0", name="ck_proposed_credit_nonneg"),
        Index("ix_verification_org_breach_status", "organization_id", "breach_detected", "status"),
    )


class AuditLog(Base, UUIDPrimaryKeyMixin):
    """Tamper-evident cryptographically chained audit ledger (SHA-256)."""

    __tablename__ = "audit_logs"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    previous_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    current_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entity_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    actor_email: Mapped[str] = mapped_column(String(255), nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    __table_args__ = (
        UniqueConstraint("organization_id", "sequence_number", name="uq_org_audit_seq"),
        Index("ix_audit_org_entity", "organization_id", "entity_type", "entity_id"),
    )
