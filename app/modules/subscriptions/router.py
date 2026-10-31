import uuid
import math
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_organization, Organization
from app.modules.subscriptions.schemas import (
    SubscriptionCreate,
    SubscriptionUpdate,
    SubscriptionPauseRequest,
    SubscriptionResumeRequest,
    SubscriptionRenewRequest,
    SubscriptionCloseRequest,
    SubscriptionResponse,
    SubscriptionPaginatedResponse,
    SubscriptionEventResponse,
    DigitalTwinResponse,
    ProductImpactRequest,
    ProductImpactResponse,
    PlanImpactRequest,
    PlanImpactResponse,
)
from app.modules.subscriptions.service import SubscriptionService
from app.modules.subscriptions.digital_twin import DigitalTwinService
from app.modules.subscriptions.impact_analysis import ChangeImpactService

subscription_router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])
impact_router = APIRouter(prefix="/change-impact", tags=["Change Impact Analysis"])


# --- Subscription Endpoints ---

@subscription_router.post("", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
def create_subscription(
    payload: SubscriptionCreate,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """Create a new subscription with pricing snapshots."""
    return SubscriptionService.create_subscription(db, org.id, payload)


@subscription_router.get("", response_model=SubscriptionPaginatedResponse)
def list_subscriptions(
    customer_id: Optional[uuid.UUID] = Query(None, description="Filter by customer ID"),
    plan_id: Optional[uuid.UUID] = Query(None, description="Filter by subscription plan ID"),
    status: Optional[str] = Query(None, description="Filter by status (DRAFT, CONFIRMED, ACTIVE, PAUSED, CLOSED, CANCELLED)"),
    search: Optional[str] = Query(None, description="Search by subscription number"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """List subscriptions with pagination and filtering."""
    items, total = SubscriptionService.list_subscriptions(
        db, org.id, customer_id=customer_id, plan_id=plan_id, status=status, search=search, page=page, per_page=per_page
    )
    pages = math.ceil(total / per_page) if per_page else 1
    return SubscriptionPaginatedResponse(items=items, total=total, page=page, per_page=per_page, pages=pages)


@subscription_router.get("/{subscription_id}", response_model=SubscriptionResponse)
def get_subscription(
    subscription_id: uuid.UUID,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """Get subscription details and items."""
    return SubscriptionService.get_subscription(db, org.id, subscription_id)


@subscription_router.patch("/{subscription_id}", response_model=SubscriptionResponse)
def update_subscription(
    subscription_id: uuid.UUID,
    payload: SubscriptionUpdate,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """Update subscription settings (such as payment terms, renewal flag)."""
    return SubscriptionService.update_subscription(db, org.id, subscription_id, payload)


@subscription_router.post("/{subscription_id}/activate", response_model=SubscriptionResponse)
def activate_subscription(
    subscription_id: uuid.UUID,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """Activate subscription and establish next billing schedule."""
    return SubscriptionService.activate_subscription(db, org.id, subscription_id)


@subscription_router.post("/{subscription_id}/pause", response_model=SubscriptionResponse)
def pause_subscription(
    subscription_id: uuid.UUID,
    payload: SubscriptionPauseRequest,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """Pause an active subscription."""
    return SubscriptionService.pause_subscription(db, org.id, subscription_id, payload)


@subscription_router.post("/{subscription_id}/resume", response_model=SubscriptionResponse)
def resume_subscription(
    subscription_id: uuid.UUID,
    payload: SubscriptionResumeRequest = SubscriptionResumeRequest(),
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """Resume a paused subscription."""
    return SubscriptionService.resume_subscription(db, org.id, subscription_id, payload)


@subscription_router.post("/{subscription_id}/renew", response_model=SubscriptionResponse)
def renew_subscription(
    subscription_id: uuid.UUID,
    payload: SubscriptionRenewRequest = SubscriptionRenewRequest(),
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """Renew an active subscription, advancing its next billing and expiry dates."""
    return SubscriptionService.renew_subscription(db, org.id, subscription_id, payload)


@subscription_router.post("/{subscription_id}/close", response_model=SubscriptionResponse)
def close_subscription(
    subscription_id: uuid.UUID,
    payload: SubscriptionCloseRequest,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """Close or terminate subscription with reason and optional early closure fee."""
    return SubscriptionService.close_subscription(db, org.id, subscription_id, payload)


@subscription_router.get("/{subscription_id}/digital-twin", response_model=DigitalTwinResponse)
def get_digital_twin(
    subscription_id: uuid.UUID,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """
    Retrieve the Subscription Digital Twin:
    A unified, real-time live view joining customer, plan, pricing snapshots,
    quotations, billing invoices, payments, and change event audit trail from actual database records.
    """
    return DigitalTwinService.get_digital_twin(db, org.id, subscription_id)


@subscription_router.get("/{subscription_id}/events", response_model=List[SubscriptionEventResponse])
def get_subscription_events(
    subscription_id: uuid.UUID,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """Retrieve complete chronological event history and audit trail for a subscription."""
    return SubscriptionService.get_events(db, org.id, subscription_id)


# --- Change Impact Analysis Endpoints ---

@impact_router.post("/product", response_model=ProductImpactResponse)
def analyze_product_impact(
    payload: ProductImpactRequest,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """Preview the impact of a proposed product price or status change before applying."""
    return ChangeImpactService.analyze_product_impact(db, org.id, payload)


@impact_router.post("/plan", response_model=PlanImpactResponse)
def analyze_plan_impact(
    payload: PlanImpactRequest,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """Preview the impact of a proposed subscription plan price or status change before applying."""
    return ChangeImpactService.analyze_plan_impact(db, org.id, payload)
