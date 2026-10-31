"""Organization and OrganizationSettings SQLAlchemy models."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional
import uuid

from sqlalchemy import ForeignKey, Index, JSON, String, Text, UniqueConstraint, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from backend.app.models.customer import Customer
    from backend.app.models.membership import Membership


class Organization(Base, TimestampMixin):
    """Organization entity representing a tenant in VERISUB."""

    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )
    phone: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    address: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    industry: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="active",
        nullable=False,
    )

    # Relationships
    settings: Mapped[Optional[OrganizationSettings]] = relationship(
        "OrganizationSettings",
        back_populates="organization",
        uselist=False,
        cascade="all, delete-orphan",
    )
    memberships: Mapped[list[Membership]] = relationship(
        "Membership",
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    customers: Mapped[list[Customer]] = relationship(
        "Customer",
        back_populates="organization",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("email", name="uq_organizations_email"),
        Index("ix_organizations_email", "email"),
        Index("ix_organizations_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<Organization(id={self.id}, name='{self.name}', status='{self.status}')>"


class OrganizationSettings(Base, TimestampMixin):
    """Organization-specific settings and preferences."""

    __tablename__ = "organization_settings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    default_currency: Mapped[str] = mapped_column(
        String(3),
        default="USD",
        nullable=False,
    )
    timezone: Mapped[str] = mapped_column(
        String(50),
        default="UTC",
        nullable=False,
    )
    tax_configuration: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
    )
    billing_preferences: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
    )

    # Relationships
    organization: Mapped[Organization] = relationship(
        "Organization",
        back_populates="settings",
    )

    __table_args__ = (
        UniqueConstraint("organization_id", name="uq_organization_settings_organization_id"),
        Index("ix_organization_settings_organization_id", "organization_id"),
    )

    def __repr__(self) -> str:
        return f"<OrganizationSettings(id={self.id}, organization_id={self.organization_id}, currency='{self.default_currency}')>"
