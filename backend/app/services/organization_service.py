"""Organization and organization settings service for VERISUB."""

from __future__ import annotations

from typing import Any, Mapping, Optional, Union
import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.permissions import RoleEnum
from backend.app.models.membership import Membership
from backend.app.models.organization import Organization, OrganizationSettings
from backend.app.models.role import MembershipRole
from backend.app.models.user import User


def create_organization(
    db: Session,
    user: User,
    payload: Union[dict[str, Any], Any],
) -> Organization:
    """Create a new organization for an authenticated user and assign them the ADMIN role."""
    data: dict[str, Any]
    if hasattr(payload, "model_dump"):
        data = payload.model_dump()
    elif isinstance(payload, dict):
        data = payload
    else:
        data = dict(payload)

    org_email = str(data["email"]).strip().lower()
    existing_org = db.query(Organization).filter(Organization.email == org_email).first()
    if existing_org:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Organization with email '{org_email}' already exists.",
        )

    org = Organization(
        id=uuid.uuid4(),
        name=str(data["name"]).strip(),
        email=org_email,
        phone=data.get("phone"),
        address=data.get("address"),
        industry=data.get("industry"),
        status="active",
    )
    db.add(org)
    db.flush()

    org_settings = OrganizationSettings(
        id=uuid.uuid4(),
        organization_id=org.id,
        default_currency="USD",
        timezone="UTC",
        tax_configuration={"tax_enabled": True, "tax_rate": 0.0},
        billing_preferences={"auto_invoice": True, "payment_terms_days": 30},
    )
    db.add(org_settings)

    membership = Membership(
        id=uuid.uuid4(),
        organization_id=org.id,
        user_id=user.id,
        status="active",
    )
    db.add(membership)
    db.flush()

    from backend.app.services.auth_service import _ensure_roles_and_permissions
    roles_by_name = _ensure_roles_and_permissions(db)
    admin_role = roles_by_name[RoleEnum.ADMIN.value]

    membership_role = MembershipRole(
        id=uuid.uuid4(),
        membership_id=membership.id,
        role_id=admin_role.id,
    )
    db.add(membership_role)
    db.commit()
    db.refresh(org)
    return org


def get_organization(db: Session, org_id: uuid.UUID) -> Organization:
    """Retrieve an organization by its unique ID.
    
    Raises HTTPException 404 if not found.
    """
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization with ID '{org_id}' not found.",
        )
    return org


def update_organization(
    db: Session,
    org_id: uuid.UUID,
    update_data: Union[dict[str, Any], Any],
) -> Organization:
    """Update organization attributes (name, phone, address, industry).

    Does not allow modifying primary email or tenant status through this method.
    """
    org = get_organization(db, org_id)

    data: dict[str, Any]
    if hasattr(update_data, "model_dump"):
        data = update_data.model_dump(exclude_unset=True)
    elif isinstance(update_data, dict):
        data = update_data
    else:
        data = dict(update_data)

    allowed_fields = {"name", "phone", "address", "industry"}
    modified = False

    for field in allowed_fields:
        if field in data and data[field] is not None:
            val = data[field]
            if isinstance(val, str):
                val = val.strip()
            setattr(org, field, val)
            modified = True

    if modified:
        db.commit()
        db.refresh(org)

    return org


def get_organization_settings(db: Session, org_id: uuid.UUID) -> OrganizationSettings:
    """Retrieve configuration settings for a given organization.

    Raises HTTPException 404 if not found.
    """
    # Verify organization exists first
    _ = get_organization(db, org_id)

    org_settings = (
        db.query(OrganizationSettings)
        .filter(OrganizationSettings.organization_id == org_id)
        .first()
    )

    if not org_settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Settings for organization '{org_id}' not found.",
        )

    return org_settings


def update_organization_settings(
    db: Session,
    org_id: uuid.UUID,
    update_data: Union[dict[str, Any], Any],
) -> OrganizationSettings:
    """Update settings (currency, timezone, tax, billing preferences) for an organization."""
    org_settings = get_organization_settings(db, org_id)

    data: dict[str, Any]
    if hasattr(update_data, "model_dump"):
        data = update_data.model_dump(exclude_unset=True)
    elif isinstance(update_data, dict):
        data = update_data
    else:
        data = dict(update_data)

    allowed_fields = {
        "default_currency",
        "timezone",
        "tax_configuration",
        "billing_preferences",
    }
    modified = False

    for field in allowed_fields:
        if field in data and data[field] is not None:
            val = data[field]
            if isinstance(val, str) and field in {"default_currency", "timezone"}:
                val = val.strip()
            setattr(org_settings, field, val)
            modified = True

    if modified:
        db.commit()
        db.refresh(org_settings)

    return org_settings
