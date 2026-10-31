"""FastAPI routers for Tax Rules, Discounts, Invoices, Payments, and Billing Runs."""

import uuid
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import (
    get_current_organization,
    get_current_user,
    require_role,
    enforce_customer_scope,
)
from app.models.auth import Organization, User, UserRole
from app.models.billing import InvoiceStatus
from app.modules.billing.schemas import (
    TaxRuleCreate,
    TaxRuleResponse,
    DiscountCreate,
    DiscountResponse,
    InvoiceCreate,
    InvoiceResponse,
    PaymentCreate,
    PaymentReceipt,
    BillingRunRequest,
    BillingRunResponse,
)
from app.modules.billing.service import BillingService
from app.modules.billing.repository import InvoiceRepository

tax_router = APIRouter(prefix="/taxes", tags=["Tax Rules"])
discount_router = APIRouter(prefix="/discounts", tags=["Discounts"])
invoice_router = APIRouter(prefix="/invoices", tags=["Invoices & Billing"])


# ── Tax Rules Endpoints ───────────────────────────────────────────────────────

@tax_router.get("", response_model=List[TaxRuleResponse])
def list_tax_rules(
    org: Organization = Depends(get_current_organization),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all tax rules defined for the organization."""
    service = BillingService(db)
    return service.list_tax_rules(org.id)


@tax_router.post("", response_model=TaxRuleResponse, status_code=status.HTTP_201_CREATED)
def create_tax_rule(
    data: TaxRuleCreate,
    org: Organization = Depends(get_current_organization),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    """Create a new tax rule. ADMIN only."""
    service = BillingService(db)
    return service.create_tax_rule(org.id, data)


# ── Discounts Endpoints ───────────────────────────────────────────────────────

@discount_router.get("", response_model=List[DiscountResponse])
def list_discounts(
    org: Organization = Depends(get_current_organization),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all discounts for the organization."""
    service = BillingService(db)
    return service.list_discounts(org.id)


@discount_router.post("", response_model=DiscountResponse, status_code=status.HTTP_201_CREATED)
def create_discount(
    data: DiscountCreate,
    org: Organization = Depends(get_current_organization),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    """Create a new promotional discount. ADMIN only."""
    service = BillingService(db)
    return service.create_discount(org.id, data)


# ── Invoices Endpoints ────────────────────────────────────────────────────────

@invoice_router.get("", response_model=List[InvoiceResponse])
def list_invoices(
    customer_id: Optional[uuid.UUID] = Query(None),
    status: Optional[InvoiceStatus] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    org: Organization = Depends(get_current_organization),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List invoices with multi-tenant and customer portal scoping."""
    # Enforce customer portal isolation: customers can only view their own invoices
    if current_user.role == UserRole.CUSTOMER:
        customer_id = current_user.customer_id

    repo = InvoiceRepository(db)
    items, _ = repo.list(org.id, customer_id=customer_id, status=status, page=page, per_page=per_page)
    return items


@invoice_router.get("/{invoice_id}", response_model=InvoiceResponse)
def get_invoice(
    invoice_id: uuid.UUID,
    org: Organization = Depends(get_current_organization),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve invoice details."""
    repo = InvoiceRepository(db)
    inv = repo.get_by_id(org.id, invoice_id)
    if not inv:
        from app.core.exceptions import EntityNotFoundException
        raise EntityNotFoundException("Invoice", str(invoice_id))

    enforce_customer_scope(current_user, inv.customer_id)
    return inv


@invoice_router.post("", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
def create_invoice(
    data: InvoiceCreate,
    org: Organization = Depends(get_current_organization),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.STAFF)),
    db: Session = Depends(get_db),
):
    """Create a new draft invoice."""
    service = BillingService(db)
    return service.create_invoice(org.id, data)


@invoice_router.post("/{invoice_id}/confirm", response_model=InvoiceResponse)
def confirm_invoice(
    invoice_id: uuid.UUID,
    org: Organization = Depends(get_current_organization),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.STAFF)),
    db: Session = Depends(get_db),
):
    """Confirm a draft invoice."""
    service = BillingService(db)
    return service.confirm_invoice(org.id, invoice_id)


@invoice_router.post("/{invoice_id}/cancel", response_model=InvoiceResponse)
def cancel_invoice(
    invoice_id: uuid.UUID,
    org: Organization = Depends(get_current_organization),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.STAFF)),
    db: Session = Depends(get_db),
):
    """Cancel an unpaid invoice."""
    service = BillingService(db)
    return service.cancel_invoice(org.id, invoice_id)


@invoice_router.post("/{invoice_id}/payments", response_model=PaymentReceipt)
def record_payment(
    invoice_id: uuid.UUID,
    data: PaymentCreate,
    org: Organization = Depends(get_current_organization),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Record a payment via the simulated payment gateway."""
    service = BillingService(db)
    return service.record_payment(org.id, invoice_id, data)


@invoice_router.post("/recurring-run", response_model=BillingRunResponse)
def trigger_billing_run(
    req: BillingRunRequest = BillingRunRequest(),
    org: Organization = Depends(get_current_organization),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    """
    Trigger an automated recurring billing run.
    Idempotent: prevents duplicate billing runs for identical billing periods.
    """
    service = BillingService(db)
    return service.run_recurring_billing(org.id, req)
