import uuid
from datetime import datetime, timezone
from typing import Optional
from fastapi import Depends, HTTPException, Header, status
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Uuid, select
from sqlalchemy.orm import Mapped, mapped_column, relationship, Session

from app.core.database import Base, get_db


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    users = relationship("User", back_populates="organization", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="admin", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    organization = relationship("Organization", back_populates="users")


def get_current_organization(
    x_organization_id: Optional[str] = Header(None, alias="X-Organization-Id"),
    db: Session = Depends(get_db),
) -> Organization:
    """
    Dependency to resolve the active organization.
    Multi-tenant isolation requires a valid organization.
    If X-Organization-Id is not supplied, auto-locates or creates the default organization for development ease.
    """
    if x_organization_id:
        try:
            org_uuid = uuid.UUID(x_organization_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid X-Organization-Id header format. Must be a valid UUID.",
            )
        org = db.get(Organization, org_uuid)
        if not org or not org.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Organization not found or inactive.",
            )
        return org

    # If no header provided, find or seed default primary organization
    default_org = db.query(Organization).filter(Organization.slug == "default-org").first()
    if not default_org:
        default_org = Organization(
            id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
            name="Default Organization",
            slug="default-org",
            is_active=True,
        )
        db.add(default_org)
        db.commit()
        db.refresh(default_org)
    return default_org


def get_current_user(
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db),
) -> User:
    """Dependency to retrieve the authenticated user within the organization."""
    if x_user_id:
        try:
            user_uuid = uuid.UUID(x_user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid X-User-Id header format. Must be a valid UUID.",
            )
        user = db.get(User, user_uuid)
        if not user or user.organization_id != org.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User not found or does not belong to active organization.",
            )
        return user

    # Default fallback user for dev/testing
    default_user = db.query(User).filter(User.organization_id == org.id).first()
    if not default_user:
        default_user = User(
            id=uuid.UUID("00000000-0000-0000-0000-000000000002"),
            organization_id=org.id,
            email=f"admin@{org.slug}.local",
            full_name="Admin User",
            role="admin",
            is_active=True,
        )
        db.add(default_user)
        db.commit()
        db.refresh(default_user)
    return default_user
