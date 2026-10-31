import uuid
import math
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_organization, Organization
from app.modules.plans.schemas import (
    PlanCreate,
    PlanUpdate,
    PlanResponse,
    PlanPaginatedResponse,
    PlanPriceHistoryResponse,
)
from app.modules.plans.service import PlanService

router = APIRouter(prefix="/plans", tags=["Subscription Plans"])


@router.post("", response_model=PlanResponse, status_code=status.HTTP_201_CREATED)
def create_plan(
    payload: PlanCreate,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """Create a subscription plan."""
    return PlanService.create_plan(db, org.id, payload)


@router.get("", response_model=PlanPaginatedResponse)
def list_plans(
    search: Optional[str] = Query(None, description="Search plan name or description"),
    status: Optional[str] = Query(None, description="Filter by status (ACTIVE, ARCHIVED, DRAFT)"),
    frequency: Optional[str] = Query(None, description="Filter by billing frequency (DAILY, WEEKLY, MONTHLY, YEARLY)"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """List plans with pagination and filtering."""
    skip = (page - 1) * per_page
    items, total = PlanService.list_plans(
        db, org.id, search=search, status=status, billing_frequency=frequency, skip=skip, limit=per_page
    )
    pages = math.ceil(total / per_page) if per_page else 1
    return PlanPaginatedResponse(items=items, total=total, page=page, per_page=per_page, pages=pages)


@router.get("/{plan_id}", response_model=PlanResponse)
def get_plan(
    plan_id: uuid.UUID,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """Get subscription plan details by ID."""
    return PlanService.get_plan(db, org.id, plan_id)


@router.patch("/{plan_id}", response_model=PlanResponse)
def update_plan(
    plan_id: uuid.UUID,
    payload: PlanUpdate,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """Update subscription plan details (price changes are preserved in history)."""
    return PlanService.update_plan(db, org.id, plan_id, payload)


@router.delete("/{plan_id}", response_model=PlanResponse)
def delete_plan(
    plan_id: uuid.UUID,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """Archive a subscription plan."""
    return PlanService.delete_or_archive_plan(db, org.id, plan_id)


@router.get("/{plan_id}/price-history", response_model=List[PlanPriceHistoryResponse])
def get_plan_price_history(
    plan_id: uuid.UUID,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """Retrieve full audit history of plan price changes."""
    return PlanService.get_price_history(db, org.id, plan_id)
