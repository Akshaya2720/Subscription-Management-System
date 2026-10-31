import uuid
import math
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_organization, Organization
from app.modules.quotations.schemas import (
    QuotationCreate,
    QuotationUpdate,
    QuotationResponse,
    QuotationPaginatedResponse,
    ConvertToSubscriptionRequest,
)
from app.modules.quotations.service import QuotationService

router = APIRouter(prefix="/quotations", tags=["Quotations"])


@router.post("", response_model=QuotationResponse, status_code=status.HTTP_201_CREATED)
def create_quotation(
    payload: QuotationCreate,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """Create a new quotation with product/variant price snapshots."""
    return QuotationService.create_quotation(db, org.id, payload)


@router.get("", response_model=QuotationPaginatedResponse)
def list_quotations(
    customer_id: Optional[uuid.UUID] = Query(None, description="Filter by customer ID"),
    status: Optional[str] = Query(None, description="Filter by status (DRAFT, CONFIRMED, CANCELLED, EXPIRED, CONVERTED)"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """List quotations with pagination and filters."""
    items, total = QuotationService.list_quotations(
        db, org.id, customer_id=customer_id, status=status, page=page, per_page=per_page
    )
    pages = math.ceil(total / per_page) if per_page else 1
    return QuotationPaginatedResponse(items=items, total=total, page=page, per_page=per_page, pages=pages)


@router.get("/{quotation_id}", response_model=QuotationResponse)
def get_quotation(
    quotation_id: uuid.UUID,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """Get quotation details and items."""
    return QuotationService.get_quotation(db, org.id, quotation_id)


@router.patch("/{quotation_id}", response_model=QuotationResponse)
def update_quotation(
    quotation_id: uuid.UUID,
    payload: QuotationUpdate,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """Update draft quotation and its items."""
    return QuotationService.update_quotation(db, org.id, quotation_id, payload)


@router.post("/{quotation_id}/confirm", response_model=QuotationResponse)
def confirm_quotation(
    quotation_id: uuid.UUID,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """Confirm a quotation, locking its agreed terms and prices."""
    return QuotationService.confirm_quotation(db, org.id, quotation_id)


@router.post("/{quotation_id}/cancel", response_model=QuotationResponse)
def cancel_quotation(
    quotation_id: uuid.UUID,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """Cancel or reject a quotation."""
    return QuotationService.cancel_quotation(db, org.id, quotation_id)


@router.post("/{quotation_id}/convert-to-subscription")
def convert_to_subscription(
    quotation_id: uuid.UUID,
    payload: ConvertToSubscriptionRequest = ConvertToSubscriptionRequest(),
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """Convert a confirmed quotation into an active/confirmed subscription."""
    sub = QuotationService.convert_to_subscription(db, org.id, quotation_id, payload)
    return {
        "message": "Quotation successfully converted to subscription.",
        "subscription_id": sub.id,
        "subscription_number": sub.subscription_number,
        "status": sub.status,
    }
