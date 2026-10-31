"""Customer, address, and contact management service for VERISUB."""

from __future__ import annotations

import math
from typing import Any, Optional, Union
import uuid

from fastapi import HTTPException, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, selectinload

from backend.app.models.customer import Customer, CustomerAddress, CustomerContact
from backend.app.models.organization import Organization


def create_customer(
    db: Session,
    org_id: uuid.UUID,
    data: Union[dict[str, Any], Any],
) -> Customer:
    """Create a new customer within a specific organization tenant.

    Enforces customer code uniqueness within the organization.
    """
    raw: dict[str, Any]
    if hasattr(data, "model_dump"):
        raw = data.model_dump(exclude_unset=True)
    elif isinstance(data, dict):
        raw = data
    else:
        raw = dict(data)

    customer_code = str(raw.get("customer_code", "")).strip()
    company_name = str(raw.get("company_name", "")).strip()

    if not customer_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="customer_code is required.",
        )
    if not company_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="company_name is required.",
        )

    # 1. Verify organization exists
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization with ID '{org_id}' not found.",
        )

    # 2. Check customer_code uniqueness within organization
    existing = (
        db.query(Customer)
        .filter(
            Customer.organization_id == org_id,
            Customer.customer_code == customer_code,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Customer with code '{customer_code}' already exists in this organization.",
        )

    # 3. Create customer record
    customer = Customer(
        organization_id=org_id,
        customer_code=customer_code,
        company_name=company_name,
        contact_name=str(raw.get("contact_name", "")).strip() if raw.get("contact_name") else None,
        email=str(raw.get("email", "")).strip().lower() if raw.get("email") else None,
        phone=str(raw.get("phone", "")).strip() if raw.get("phone") else None,
        billing_address=raw.get("billing_address"),
        tax_identifier=str(raw.get("tax_identifier", "")).strip() if raw.get("tax_identifier") else None,
        status=str(raw.get("status", "active")).strip().lower() if raw.get("status") else "active",
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


def list_customers(
    db: Session,
    org_id: uuid.UUID,
    page: int = 1,
    page_size: int = 20,
    search: Optional[str] = None,
    status: Optional[str] = None,
) -> dict[str, Any]:
    """List customers with strict tenant isolation, search filtering, and pagination."""
    page = max(1, page)
    page_size = max(1, min(page_size, 100))

    # CRITICAL: Always filter by org_id for strict tenant isolation
    query = db.query(Customer).filter(Customer.organization_id == org_id)

    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Customer.company_name.ilike(term),
                Customer.contact_name.ilike(term),
                Customer.customer_code.ilike(term),
                Customer.email.ilike(term),
            )
        )

    if status and status.strip():
        query = query.filter(Customer.status == status.strip().lower())

    total = query.count()
    offset = (page - 1) * page_size
    items = (
        query.order_by(Customer.created_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )

    total_pages = math.ceil(total / page_size) if page_size > 0 else 0

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


def get_customer(
    db: Session,
    customer_id: uuid.UUID,
    org_id: uuid.UUID,
) -> Customer:
    """Retrieve a customer ensuring tenant isolation and eager loading addresses and contacts."""
    customer = (
        db.query(Customer)
        .options(
            selectinload(Customer.addresses),
            selectinload(Customer.contacts),
        )
        .filter(
            Customer.id == customer_id,
            Customer.organization_id == org_id,
        )
        .first()
    )

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with ID '{customer_id}' not found in this organization.",
        )

    return customer


def update_customer(
    db: Session,
    customer_id: uuid.UUID,
    org_id: uuid.UUID,
    update_data: Union[dict[str, Any], Any],
) -> Customer:
    """Update customer details ensuring tenant isolation."""
    customer = get_customer(db, customer_id, org_id)

    raw: dict[str, Any]
    if hasattr(update_data, "model_dump"):
        raw = update_data.model_dump(exclude_unset=True)
    elif isinstance(update_data, dict):
        raw = update_data
    else:
        raw = dict(update_data)

    allowed_fields = {
        "company_name",
        "contact_name",
        "email",
        "phone",
        "billing_address",
        "tax_identifier",
        "status",
    }
    modified = False

    for field in allowed_fields:
        if field in raw and raw[field] is not None:
            val = raw[field]
            if isinstance(val, str):
                val = val.strip()
                if field == "email":
                    val = val.lower()
                elif field == "status":
                    val = val.lower()
                    if val not in {"active", "inactive", "suspended"}:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="status must be one of: 'active', 'inactive', 'suspended'",
                        )
            setattr(customer, field, val)
            modified = True

    if modified:
        db.commit()
        db.refresh(customer)

    return customer


def delete_customer(
    db: Session,
    customer_id: uuid.UUID,
    org_id: uuid.UUID,
) -> dict[str, str]:
    """Soft-delete a customer by setting status to 'inactive'."""
    customer = get_customer(db, customer_id, org_id)
    customer.status = "inactive"
    db.commit()

    return {"message": "Customer deactivated successfully."}


def add_customer_address(
    db: Session,
    customer_id: uuid.UUID,
    org_id: uuid.UUID,
    address_data: Union[dict[str, Any], Any],
) -> CustomerAddress:
    """Add a delivery or billing address for a customer."""
    customer = get_customer(db, customer_id, org_id)

    raw: dict[str, Any]
    if hasattr(address_data, "model_dump"):
        raw = address_data.model_dump(exclude_unset=True)
    elif isinstance(address_data, dict):
        raw = address_data
    else:
        raw = dict(address_data)

    address_type = str(raw.get("address_type", "billing")).strip().lower()
    if address_type not in {"billing", "shipping", "both"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="address_type must be one of: 'billing', 'shipping', 'both'",
        )

    is_default = bool(raw.get("is_default", False))
    if is_default:
        # Clear default flag on existing addresses of the same type for this customer
        db.query(CustomerAddress).filter(
            CustomerAddress.customer_id == customer.id,
            CustomerAddress.address_type == address_type,
        ).update({"is_default": False})

    address = CustomerAddress(
        customer_id=customer.id,
        address_type=address_type,
        street=str(raw.get("street", "")).strip() if raw.get("street") else None,
        city=str(raw.get("city", "")).strip() if raw.get("city") else None,
        state=str(raw.get("state", "")).strip() if raw.get("state") else None,
        postal_code=str(raw.get("postal_code", "")).strip() if raw.get("postal_code") else None,
        country=str(raw.get("country", "")).strip() if raw.get("country") else None,
        is_default=is_default,
    )
    db.add(address)
    db.commit()
    db.refresh(address)
    return address


def add_customer_contact(
    db: Session,
    customer_id: uuid.UUID,
    org_id: uuid.UUID,
    contact_data: Union[dict[str, Any], Any],
) -> CustomerContact:
    """Add a point of contact for a customer."""
    customer = get_customer(db, customer_id, org_id)

    raw: dict[str, Any]
    if hasattr(contact_data, "model_dump"):
        raw = contact_data.model_dump(exclude_unset=True)
    elif isinstance(contact_data, dict):
        raw = contact_data
    else:
        raw = dict(contact_data)

    full_name = str(raw.get("full_name", "")).strip()
    if not full_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="full_name is required for customer contact.",
        )

    is_primary = bool(raw.get("is_primary", False))
    if is_primary:
        # Clear primary flag on other contacts for this customer
        db.query(CustomerContact).filter(
            CustomerContact.customer_id == customer.id,
        ).update({"is_primary": False})

    contact = CustomerContact(
        customer_id=customer.id,
        full_name=full_name,
        email=str(raw.get("email", "")).strip().lower() if raw.get("email") else None,
        phone=str(raw.get("phone", "")).strip() if raw.get("phone") else None,
        role=str(raw.get("role", "")).strip() if raw.get("role") else None,
        is_primary=is_primary,
    )
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact
