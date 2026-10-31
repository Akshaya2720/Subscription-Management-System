"""Organization and tenant settings router for VERISUB."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.app.core.permissions import PermissionEnum
from backend.app.db.session import get_db
from backend.app.dependencies.auth import get_current_membership, require_permissions
from backend.app.models.membership import Membership
from backend.app.models.organization import Organization, OrganizationSettings
from backend.app.schemas.organization import (
    OrganizationResponse,
    OrganizationSettingsResponse,
    OrganizationSettingsUpdate,
    OrganizationUpdate,
)
from backend.app.services import organization_service

router = APIRouter(prefix="/api/v1/organizations", tags=["Organizations"])


@router.get(
    "/current",
    response_model=OrganizationResponse,
    summary="Retrieve current organization profile",
)
def get_current_organization(
    membership: Membership = Depends(get_current_membership),
    db: Session = Depends(get_db),
) -> Organization:
    """Retrieve details of the active tenant organization context.

    Requires authenticated user with active membership in the organization.
    """
    return organization_service.get_organization(
        db=db,
        org_id=membership.organization_id,
    )


@router.patch(
    "/current",
    response_model=OrganizationResponse,
    summary="Update current organization profile",
)
def update_current_organization(
    payload: OrganizationUpdate,
    membership: Membership = Depends(
        require_permissions(PermissionEnum.MANAGE_ORGANIZATION)
    ),
    db: Session = Depends(get_db),
) -> Organization:
    """Update editable organization attributes (name, phone, address, industry).

    Requires MANAGE_ORGANIZATION permission.
    """
    return organization_service.update_organization(
        db=db,
        org_id=membership.organization_id,
        update_data=payload,
    )


@router.get(
    "/current/settings",
    response_model=OrganizationSettingsResponse,
    summary="Retrieve organization configuration settings",
)
def get_current_organization_settings(
    membership: Membership = Depends(
        require_permissions(PermissionEnum.MANAGE_SETTINGS)
    ),
    db: Session = Depends(get_db),
) -> OrganizationSettings:
    """Retrieve billing, tax, currency, and timezone settings for the active organization.

    Requires MANAGE_SETTINGS permission.
    """
    return organization_service.get_organization_settings(
        db=db,
        org_id=membership.organization_id,
    )


@router.patch(
    "/current/settings",
    response_model=OrganizationSettingsResponse,
    summary="Update organization configuration settings",
)
def update_current_organization_settings(
    payload: OrganizationSettingsUpdate,
    membership: Membership = Depends(
        require_permissions(PermissionEnum.MANAGE_SETTINGS)
    ),
    db: Session = Depends(get_db),
) -> OrganizationSettings:
    """Update settings including default currency, timezone, tax, and billing preferences.

    Requires MANAGE_SETTINGS permission.
    """
    return organization_service.update_organization_settings(
        db=db,
        org_id=membership.organization_id,
        update_data=payload,
    )
