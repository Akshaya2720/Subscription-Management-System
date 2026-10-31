"""Role, Permission, and RBAC association SQLAlchemy models."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional
import uuid

from sqlalchemy import ForeignKey, Index, String, UniqueConstraint, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base

if TYPE_CHECKING:
    from backend.app.models.membership import Membership


class Role(Base):
    """Role entity representing an access level or persona."""

    __tablename__ = "roles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    # Relationships
    role_permissions: Mapped[list[RolePermission]] = relationship(
        "RolePermission",
        back_populates="role",
        cascade="all, delete-orphan",
    )
    membership_roles: Mapped[list[MembershipRole]] = relationship(
        "MembershipRole",
        back_populates="role",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("name", name="uq_roles_name"),
        Index("ix_roles_name", "name", unique=True),
    )

    def __repr__(self) -> str:
        return f"<Role(id={self.id}, name='{self.name}')>"


class Permission(Base):
    """Permission entity defining an atomic privilege."""

    __tablename__ = "permissions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    permission_name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    # Relationships
    role_permissions: Mapped[list[RolePermission]] = relationship(
        "RolePermission",
        back_populates="permission",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("permission_name", name="uq_permissions_name"),
        Index("ix_permissions_name", "permission_name", unique=True),
    )

    def __repr__(self) -> str:
        return f"<Permission(id={self.id}, permission_name='{self.permission_name}')>"


class RolePermission(Base):
    """Association table mapping roles to permissions."""

    __tablename__ = "role_permissions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
    )
    permission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("permissions.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Relationships
    role: Mapped[Role] = relationship(
        "Role",
        back_populates="role_permissions",
    )
    permission: Mapped[Permission] = relationship(
        "Permission",
        back_populates="role_permissions",
    )

    __table_args__ = (
        UniqueConstraint("role_id", "permission_id", name="uq_role_permissions_role_id_permission_id"),
        Index("ix_role_permissions_role_id", "role_id"),
        Index("ix_role_permissions_permission_id", "permission_id"),
    )

    def __repr__(self) -> str:
        return f"<RolePermission(id={self.id}, role_id={self.role_id}, permission_id={self.permission_id})>"


class MembershipRole(Base):
    """Association table mapping memberships to roles."""

    __tablename__ = "membership_roles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    membership_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("memberships.id", ondelete="CASCADE"),
        nullable=False,
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Relationships
    membership: Mapped[Membership] = relationship(
        "Membership",
        back_populates="membership_roles",
    )
    role: Mapped[Role] = relationship(
        "Role",
        back_populates="membership_roles",
    )

    __table_args__ = (
        UniqueConstraint("membership_id", "role_id", name="uq_membership_roles_membership_id_role_id"),
        Index("ix_membership_roles_membership_id", "membership_id"),
        Index("ix_membership_roles_role_id", "role_id"),
    )

    def __repr__(self) -> str:
        return f"<MembershipRole(id={self.id}, membership_id={self.membership_id}, role_id={self.role_id})>"
