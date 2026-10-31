"""Authentication and Multi-Tenant Context Dependencies for VERISUB."""

import uuid
from typing import Optional
from fastapi import Depends, HTTPException, Header, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.auth import Organization, User, UserRole


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
            password_hash="argon2id_dev_dummy_hash",
            full_name="Admin User",
            role=UserRole.ADMIN,
            is_active=True,
        )
        db.add(default_user)
        db.commit()
        db.refresh(default_user)
    return default_user
