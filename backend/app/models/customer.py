"""Customer, CustomerAddress, and CustomerContact SQLAlchemy models."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional
import uuid

from sqlalchemy import Boolean, ForeignKey, Index, String, Text, UniqueConstraint, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from backend.app.models.organization import Organization


class Customer(Base, TimestampMixin):
    """Customer entity representing a client or subscriber organization."""

    __tablename__ = "customers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    customer_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    company_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    contact_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    email: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    phone: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    billing_address: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    tax_identifier: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="active",
        nullable=False,
    )

    # Relationships
    organization: Mapped[Organization] = relationship(
        "Organization",
        back_populates="customers",
    )
    addresses: Mapped[list[CustomerAddress]] = relationship(
        "CustomerAddress",
        back_populates="customer",
        cascade="all, delete-orphan",
    )
    contacts: Mapped[list[CustomerContact]] = relationship(
        "CustomerContact",
        back_populates="customer",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("organization_id", "customer_code", name="uq_customers_organization_customer_code"),
        Index("ix_customers_organization_id", "organization_id"),
        Index("ix_customers_customer_code", "customer_code"),
        Index("ix_customers_email", "email"),
        Index("ix_customers_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<Customer(id={self.id}, code='{self.customer_code}', company='{self.company_name}')>"


class CustomerAddress(Base, TimestampMixin):
    """Customer address record for billing, shipping, or physical location."""

    __tablename__ = "customer_addresses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
    )
    address_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    street: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    city: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    state: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    postal_code: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )
    country: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    is_default: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Relationships
    customer: Mapped[Customer] = relationship(
        "Customer",
        back_populates="addresses",
    )

    __table_args__ = (
        Index("ix_customer_addresses_customer_id", "customer_id"),
    )

    def __repr__(self) -> str:
        return f"<CustomerAddress(id={self.id}, customer_id={self.customer_id}, type='{self.address_type}')>"


class CustomerContact(Base, TimestampMixin):
    """Customer point of contact representation."""

    __tablename__ = "customer_contacts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
    )
    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    email: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    phone: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    role: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Relationships
    customer: Mapped[Customer] = relationship(
        "Customer",
        back_populates="contacts",
    )

    __table_args__ = (
        Index("ix_customer_contacts_customer_id", "customer_id"),
    )

    def __repr__(self) -> str:
        return f"<CustomerContact(id={self.id}, customer_id={self.customer_id}, name='{self.full_name}')>"
