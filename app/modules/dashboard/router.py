"""Router for finance dashboard metrics."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_organization, require_role
from app.models.auth import Organization, UserRole
from app.modules.dashboard.schemas import DashboardMetricsResponse
from app.modules.dashboard.service import DashboardService

dashboard_router = APIRouter(prefix="/dashboard", tags=["Finance Dashboard"])


@dashboard_router.get("/metrics", response_model=DashboardMetricsResponse)
def get_dashboard_metrics(
    range: str = Query("30d", description="Metric date range e.g. 7d, 30d, 90d, 1y"),
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
    _role: str = Depends(require_role(UserRole.ADMIN, UserRole.STAFF)),
):
    """Retrieve high-performance aggregated metrics for the Finance Dashboard."""
    return DashboardService.get_metrics(db, org.id, date_range=range)
