"""Customer management router for VERISUB."""

from __future__ import annotations

from typing import Any, Optional
import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.app.core.permissions import PermissionEnum
from backend.app.db.session import get_db
from backend.app.dependencies.auth import require_permissions
from backend.app.models.customer import Customer, CustomerAddress, CustomerContact
from backend.app.models.membership import Membership
from backend.app.schemas.common import MessageResponse, PaginatedResponse
from backend.app.schemas.customer import (
    CustomerAddressCreate,
    CustomerAddressResponse,
    CustomerContactCreate,
    CustomerContactResponse,
    CustomerCreate,
    CustomerResponse,
    CustomerUpdate,
)
from backend.app.services import customer_service

router = APIRouter(prefix="/api/v1/customers", tags=["Customers"])


@router.post(
    "/",
    response_model=CustomerResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new customer",
)
def create_customer(
    payload: CustomerCreate,
    membership: Membership = Depends(
        require_permissions(PermissionEnum.MANAGE_CUSTOMERS)
    ),
    db: Session = Depends(get_db),
) -> Customer:
    """Create a new customer record within the tenant organization.

    Requires MANAGE_CUSTOMERS permission.
    """
    return customer_service.create_customer(
        db=db,
        org_id=membership.organization_id,
        data=payload,
    )


@router.get(
    "/",
    response_model=PaginatedResponse[CustomerResponse],
    summary="List organization customers",
)
def list_customers(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(default=None, description="Search by name, email, or code"),
    status: Optional[str] = Query(default=None, description="Filter by status (active, inactive, suspended)"),
    membership: Membership = Depends(
        require_permissions(PermissionEnum.MANAGE_CUSTOMERS)
    ),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Retrieve paginated list of customers for the current organization.

    Requires MANAGE_CUSTOMERS permission.
    """
    return customer_service.list_customers(
        db=db,
        org_id=membership.organization_id,
        page=page,
        page_size=page_size,
        search=search,
        status=status,
    )


@router.get(
    "/{customer_id}",
    response_model=CustomerResponse,
    summary="Retrieve customer details by ID",
)
def get_customer(
    customer_id: uuid.UUID,
    membership: Membership = Depends(
        require_permissions(PermissionEnum.MANAGE_CUSTOMERS)
    ),
    db: Session = Depends(get_db),
) -> Customer:
    """Retrieve customer details by ID within the current organization.

    Requires MANAGE_CUSTOMERS permission.
    """
    return customer_service.get_customer(
        db=db,
        customer_id=customer_id,
        org_id=membership.organization_id,
    )


@router.patch(
    "/{customer_id}",
    response_model=CustomerResponse,
    summary="Update customer details",
)
def update_customer(
    customer_id: uuid.UUID,
    payload: CustomerUpdate,
    membership: Membership = Depends(
        require_permissions(PermissionEnum.MANAGE_CUSTOMERS)
    ),
    db: Session = Depends(get_db),
) -> Customer:
    """Update customer details within the current organization.

    Requires MANAGE_CUSTOMERS permission.
    """
    return customer_service.update_customer(
        db=db,
        customer_id=customer_id,
        org_id=membership.organization_id,
        update_data=payload,
    )


@router.delete(
    "/{customer_id}",
    response_model=MessageResponse,
    summary="Deactivate customer",
)
def delete_customer(
    customer_id: uuid.UUID,
    membership: Membership = Depends(
        require_permissions(PermissionEnum.MANAGE_CUSTOMERS)
    ),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Deactivate (soft-delete) a customer by setting status to inactive.

    Requires MANAGE_CUSTOMERS permission.
    """
    res = customer_service.delete_customer(
        db=db,
        customer_id=customer_id,
        org_id=membership.organization_id,
    )
    if isinstance(res, dict) and "message" in res:
        return res
    return {"message": "Customer deactivated successfully."}


@router.post(
    "/{customer_id}/addresses",
    response_model=CustomerAddressResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add an address for a customer",
)
def add_customer_address(
    customer_id: uuid.UUID,
    payload: CustomerAddressCreate,
    membership: Membership = Depends(
        require_permissions(PermissionEnum.MANAGE_CUSTOMERS)
    ),
    db: Session = Depends(get_db),
) -> CustomerAddress:
    """Add a billing or shipping address for the specified customer.

    Requires MANAGE_CUSTOMERS permission.
    """
    return customer_service.add_customer_address(
        db=db,
        customer_id=customer_id,
        org_id=membership.organization_id,
        address_data=payload,
    )


@router.post(
    "/{customer_id}/contacts",
    response_model=CustomerContactResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a contact person for a customer",
)
def add_customer_contact(
    customer_id: uuid.UUID,
    payload: CustomerContactCreate,
    membership: Membership = Depends(
        require_permissions(PermissionEnum.MANAGE_CUSTOMERS)
    ),
    db: Session = Depends(get_db),
) -> CustomerContact:
    """Add a contact person for the specified customer.

    Requires MANAGE_CUSTOMERS permission.
    """
    return customer_service.add_customer_contact(
        db=db,
        customer_id=customer_id,
        org_id=membership.organization_id,
        contact_data=payload,
    )
