import uuid
import math
from typing import Optional, List, Any
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_organization, Organization
from app.modules.customers.schemas import (
    CustomerCreate,
    CustomerUpdate,
    CustomerResponse,
    CustomerPaginatedResponse,
)
from app.modules.customers.service import CustomerService

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.post("", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
def create_customer(
    payload: CustomerCreate,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """Create a new customer within the organization."""
    return CustomerService.create_customer(db, org.id, payload)


@router.get("", response_model=CustomerPaginatedResponse)
def list_customers(
    search: Optional[str] = Query(None, description="Search by customer code, company, contact name, or email"),
    status: Optional[str] = Query(None, description="Filter by status (ACTIVE, INACTIVE, SUSPENDED)"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """List and search customers with pagination and filtering."""
    items, total = CustomerService.list_customers(
        db, org.id, search=search, status=status, page=page, per_page=per_page
    )
    pages = math.ceil(total / per_page) if per_page else 1
    return CustomerPaginatedResponse(items=items, total=total, page=page, per_page=per_page, pages=pages)


@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(
    customer_id: uuid.UUID,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """Get customer details by ID."""
    return CustomerService.get_customer(db, org.id, customer_id)


@router.patch("/{customer_id}", response_model=CustomerResponse)
def update_customer(
    customer_id: uuid.UUID,
    payload: CustomerUpdate,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """Update customer details."""
    return CustomerService.update_customer(db, org.id, customer_id, payload)


@router.delete("/{customer_id}", response_model=CustomerResponse)
def delete_customer(
    customer_id: uuid.UUID,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """Deactivate or delete customer record."""
    return CustomerService.delete_or_deactivate_customer(db, org.id, customer_id)


@router.get("/{customer_id}/invoices")
def get_customer_invoices(
    customer_id: uuid.UUID,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """Retrieve billing invoice history for a customer."""
    invoices = CustomerService.get_customer_invoices(db, org.id, customer_id)
    return [
        {
            "id": inv.id,
            "invoice_number": inv.invoice_number,
            "issue_date": inv.issue_date,
            "due_date": inv.due_date,
            "subtotal": inv.subtotal,
            "discount_total": inv.discount_total,
            "tax_total": inv.tax_total,
            "total_amount": inv.total_amount,
            "status": inv.status,
            "verification_status": inv.verification_status,
        }
        for inv in invoices
    ]


@router.get("/{customer_id}/subscriptions")
def get_customer_subscriptions(
    customer_id: uuid.UUID,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """Retrieve all subscriptions associated with this customer."""
    from app.modules.subscriptions.models import Subscription

    CustomerService.get_customer(db, org.id, customer_id)
    subscriptions = (
        db.query(Subscription)
        .filter(Subscription.organization_id == org.id, Subscription.customer_id == customer_id)
        .order_by(Subscription.created_at.desc())
        .all()
    )
    return [
        {
            "id": s.id,
            "subscription_number": s.subscription_number,
            "status": s.status,
            "billing_frequency": s.billing_frequency,
            "start_date": s.start_date,
            "next_billing_date": s.next_billing_date,
            "expiry_date": s.expiry_date,
            "renewal_enabled": s.renewal_enabled,
        }
        for s in subscriptions
    ]
