"""Organization and organization settings service for VERISUB."""

from __future__ import annotations

from typing import Any, Mapping, Optional, Union
import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.app.models.organization import Organization, OrganizationSettings


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
