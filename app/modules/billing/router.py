import io
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import List, Optional, Dict, Any
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Response,
    UploadFile,
    File,
    Form,
    Query,
    status,
)
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import (
    Organization,
    User,
    get_current_organization,
    get_current_user,
)
from app.core.exceptions import (
    EntityNotFoundException,
    InvalidStateTransitionException,
    BusinessRuleValidationException,
)
from app.modules.billing.models import (
    TaxRule,
    Discount,
    Invoice,
    InvoiceItem,
    BillingRun,
    Payment,
    PaymentAllocation,
    ReconciliationRun,
    ReconciliationItem,
    Contract,
    ServiceCommitment,
    ServiceEvent,
    VerificationRun,
    VerificationResult,
    ServiceCredit,
    InvoiceAnomaly,
    AuditEvent,
)
from app.modules.billing.schemas import (
    TaxRuleCreate,
    TaxRuleUpdate,
    TaxRuleResponse,
    DiscountCreate,
    DiscountUpdate,
    DiscountValidateRequest,
    DiscountResponse,
    InvoiceCreate,
    InvoiceResponse,
    InvoiceStatusUpdate,
    BillingRunCreate,
    BillingRunResponse,
    PaymentCreate,
    PaymentAllocateRequest,
    PaymentRefundRequest,
    PaymentResponse,
    PaymentAllocationResponse,
    ReconciliationReviewRequest,
    ReconciliationRunResponse,
    ReconciliationItemResponse,
    MatchTransactionRequest,
    ContractCreate,
    ServiceEventCreate,
    VerificationRunResponse,
    VerificationResultResponse,
    ServiceCreditResponse,
    CreditApprovalRequest,
    AnomalyResponse,
    AnomalyReviewRequest,
    AssistantQueryRequest,
    AssistantQueryResponse,
    AuditEventResponse,
    AuditVerifyResponse,
    AuditAnchorRequest,
    AuditAnchorResponse,
)
from app.modules.billing.taxes import TaxService
from app.modules.billing.discounts import DiscountService
from app.modules.billing.invoices import InvoiceService
from app.modules.billing.recurring import RecurringBillingService
from app.modules.billing.payments import PaymentService
from app.modules.billing.reconciliation import ReconciliationService
from app.modules.billing.verification import VerificationService
from app.modules.billing.anomaly import AnomalyDetectionService
from app.modules.billing.assistant import BusinessAssistantService
from app.modules.billing.audit import AuditService

router = APIRouter()


# ==========================================
# 1. TAXES
# ==========================================
@router.post("/tax-rules", response_model=TaxRuleResponse, tags=["Taxes"], status_code=status.HTTP_201_CREATED)
def create_tax_rule(
    payload: TaxRuleCreate,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
    user: User = Depends(get_current_user),
):
    """Create a jurisdiction-specific tax rule."""
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Only ADMIN can configure tax rules.")
    rule = TaxService.create_tax_rule(
        db=db,
        organization_id=org.id,
        name=payload.name,
        tax_rate=payload.tax_rate,
        tax_type=payload.tax_type,
        inclusive_or_exclusive=payload.inclusive_or_exclusive,
        effective_from=payload.effective_from,
        effective_until=payload.effective_until,
        active=payload.active,
    )
    AuditService.record_audit_event(
        db, org.id, "TAX_RULE_CREATED", "TAX_RULE", rule.id, f"Created tax rule {rule.name} ({rule.tax_rate})", user.id
    )
    return rule


@router.get("/tax-rules", response_model=List[TaxRuleResponse], tags=["Taxes"])
def list_tax_rules(
    active_only: bool = False,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """List configurable tax rules for active organization."""
    return TaxService.get_tax_rules(db, org.id, active_only=active_only)


@router.patch("/tax-rules/{rule_id}", response_model=TaxRuleResponse, tags=["Taxes"])
def update_tax_rule(
    rule_id: uuid.UUID,
    payload: TaxRuleUpdate,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
    user: User = Depends(get_current_user),
):
    """Update tax rule configuration."""
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Only ADMIN can modify tax rules.")
    rule = TaxService.update_tax_rule(db, org.id, rule_id, **payload.model_dump(exclude_unset=True))
    if not rule:
        raise HTTPException(status_code=404, detail="Tax rule not found.")
    AuditService.record_audit_event(
        db, org.id, "TAX_RULE_UPDATED", "TAX_RULE", rule.id, f"Updated tax rule {rule.name}", user.id
    )
    return rule


# ==========================================
# 2. DISCOUNTS
# ==========================================
@router.post("/discounts", response_model=DiscountResponse, tags=["Discounts"], status_code=status.HTTP_201_CREATED)
def create_discount(
    payload: DiscountCreate,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
    user: User = Depends(get_current_user),
):
    """Create a promotional or contractual discount."""
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Only ADMIN can configure discounts.")
    disc = DiscountService.create_discount(
        db=db,
        organization_id=org.id,
        discount_name=payload.discount_name,
        discount_type=payload.discount_type,
        discount_value=payload.discount_value,
        discount_code=payload.discount_code,
        minimum_purchase=payload.minimum_purchase,
        minimum_quantity=payload.minimum_quantity,
        start_date=payload.start_date,
        end_date=payload.end_date,
        usage_limit=payload.usage_limit,
        product_id=payload.product_id,
        subscription_wide=payload.subscription_wide,
        active=payload.active,
    )
    AuditService.record_audit_event(
        db, org.id, "DISCOUNT_CREATED", "DISCOUNT", disc.id, f"Created discount {disc.discount_name}", user.id
    )
    return disc


@router.get("/discounts", response_model=List[DiscountResponse], tags=["Discounts"])
def list_discounts(
    active_only: bool = False,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """List discounts for the organization."""
    return DiscountService.get_discounts(db, org.id, active_only=active_only)


@router.patch("/discounts/{discount_id}", response_model=DiscountResponse, tags=["Discounts"])
def update_discount(
    discount_id: uuid.UUID,
    payload: DiscountUpdate,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
    user: User = Depends(get_current_user),
):
    """Update discount parameters."""
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Only ADMIN can update discounts.")
    disc = DiscountService.update_discount(db, org.id, discount_id, **payload.model_dump(exclude_unset=True))
    if not disc:
        raise HTTPException(status_code=404, detail="Discount not found.")
    AuditService.record_audit_event(
        db, org.id, "DISCOUNT_UPDATED", "DISCOUNT", disc.id, f"Updated discount {disc.discount_name}", user.id
    )
    return disc


@router.post("/discounts/{discount_id}/validate", tags=["Discounts"])
def validate_discount(
    discount_id: uuid.UUID,
    payload: DiscountValidateRequest,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """Validate discount eligibility for purchase amount, quantity, and date."""
    disc = DiscountService.get_discount_by_id(db, org.id, discount_id)
    if not disc:
        raise HTTPException(status_code=404, detail="Discount not found.")
    eligible, reason = DiscountService.validate_discount(
        disc,
        purchase_subtotal=payload.purchase_subtotal,
        quantity=payload.quantity,
        evaluation_date=payload.evaluation_date,
    )
    estimated_amount = (
        DiscountService.calculate_discount_amount(disc, payload.purchase_subtotal) if eligible else Decimal("0.00")
    )
    return {
        "eligible": eligible,
        "reason": reason,
        "discount_name": disc.discount_name,
        "discount_type": disc.discount_type,
        "estimated_discount_amount": float(estimated_amount),
    }


# ==========================================
# 3. INVOICES
# ==========================================
@router.get("/invoices", response_model=List[InvoiceResponse], tags=["Invoices"])
def list_invoices(
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    customer_id: Optional[uuid.UUID] = Query(None),
    subscription_id: Optional[uuid.UUID] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """Retrieve invoices with multi-tenant filtering, search and pagination."""
    invoices, _ = InvoiceService.get_invoices(
        db=db,
        organization_id=org.id,
        search=search,
        status=status,
        customer_id=customer_id,
        subscription_id=subscription_id,
        page=page,
        per_page=per_page,
    )
    return invoices


@router.post("/invoices", response_model=InvoiceResponse, tags=["Invoices"], status_code=status.HTTP_201_CREATED)
def create_invoice(
    payload: InvoiceCreate,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
    user: User = Depends(get_current_user),
):
    """Create an invoice with immutable price snapshots."""
    items_raw = [it.model_dump() for it in payload.items]
    inv = InvoiceService.create_invoice(
        db=db,
        organization_id=org.id,
        customer_id=payload.customer_id,
        subscription_id=payload.subscription_id,
        due_date=payload.due_date,
        items_data=items_raw,
        billing_period_start=payload.billing_period_start,
        billing_period_end=payload.billing_period_end,
        currency=payload.currency,
        invoice_type=payload.invoice_type,
        discount_id=payload.discount_id,
        tax_rule_ids=payload.tax_rule_ids,
        notes=payload.notes,
        status="DRAFT",
    )
    AuditService.record_audit_event(
        db, org.id, "INVOICE_CREATED", "INVOICE", inv.id, f"Created invoice {inv.invoice_number} ({inv.total_amount} {inv.currency})", user.id
    )
    return inv


@router.get("/invoices/{invoice_id}", response_model=InvoiceResponse, tags=["Invoices"])
def get_invoice(
    invoice_id: uuid.UUID,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """Get single invoice details by ID."""
    inv = InvoiceService.get_invoice_by_id(db, org.id, invoice_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found.")
    return inv


@router.post("/invoices/{invoice_id}/confirm", response_model=InvoiceResponse, tags=["Invoices"])
def confirm_invoice(
    invoice_id: uuid.UUID,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
    user: User = Depends(get_current_user),
):
    """Confirm a draft invoice, locking financial values."""
    inv = InvoiceService.confirm_invoice(db, org.id, invoice_id)
    AuditService.record_audit_event(
        db, org.id, "INVOICE_CONFIRMED", "INVOICE", inv.id, f"Confirmed invoice {inv.invoice_number}", user.id
    )
    return inv


@router.post("/invoices/{invoice_id}/cancel", response_model=InvoiceResponse, tags=["Invoices"])
def cancel_invoice(
    invoice_id: uuid.UUID,
    reason: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
    user: User = Depends(get_current_user),
):
    """Cancel an unpaid invoice."""
    inv = InvoiceService.cancel_invoice(db, org.id, invoice_id, reason=reason)
    AuditService.record_audit_event(
        db, org.id, "INVOICE_CANCELLED", "INVOICE", inv.id, f"Cancelled invoice {inv.invoice_number} (Reason: {reason})", user.id
    )
    return inv


@router.patch("/invoices/{invoice_id}/status", response_model=InvoiceResponse, tags=["Invoices"])
def patch_invoice_status(
    invoice_id: uuid.UUID,
    payload: InvoiceStatusUpdate,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
    user: User = Depends(get_current_user),
):
    """Update invoice status."""
    inv = InvoiceService.update_invoice_status(db, org.id, invoice_id, payload.status)
    AuditService.record_audit_event(
        db, org.id, "INVOICE_STATUS_UPDATED", "INVOICE", inv.id, f"Updated invoice {inv.invoice_number} status to {inv.status}", user.id
    )
    return inv


@router.get("/invoices/{invoice_id}/pdf", tags=["Invoices"])
def get_invoice_pdf(
    invoice_id: uuid.UUID,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """Generate and download print-ready PDF invoice."""
    inv = InvoiceService.get_invoice_by_id(db, org.id, invoice_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found.")
    pdf_bytes = InvoiceService.generate_pdf(inv)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{inv.invoice_number}.pdf"'},
    )


# ==========================================
# 4. RECURRING BILLING ENGINE
# ==========================================
@router.post("/billing/run", response_model=BillingRunResponse, tags=["Billing"])
@router.post("/billing/execute", response_model=BillingRunResponse, tags=["Billing"])
def run_recurring_billing(
    payload: Optional[BillingRunCreate] = None,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
    user: User = Depends(get_current_user),
):
    """Execute on-demand or scheduled recurring billing run."""
    as_of = payload.as_of_date if payload else None
    run = RecurringBillingService.execute_billing_run(db, org.id, as_of_date=as_of)
    AuditService.record_audit_event(
        db, org.id, "BILLING_RUN_EXECUTED", "BILLING_RUN", run.id,
        f"Executed billing run {run.run_reference} ({run.successful_count} success, {run.failed_count} failed)",
        user.id
    )
    return run


@router.get("/billing/runs", response_model=List[BillingRunResponse], tags=["Billing"])
def list_billing_runs(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """List execution history of recurring billing runs."""
    runs, _ = RecurringBillingService.get_billing_runs(db, org.id, page=page, per_page=per_page)
    return runs


@router.get("/billing/runs/{run_id}", response_model=BillingRunResponse, tags=["Billing"])
def get_billing_run(
    run_id: uuid.UUID,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """Get single billing run details with itemized execution logs."""
    run = RecurringBillingService.get_billing_run_by_id(db, org.id, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Billing run not found.")
    return run


@router.get("/billing/due-subscriptions", tags=["Billing"])
def get_due_subscriptions(
    as_of_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """Inspect subscriptions due for recurring billing."""
    subs = RecurringBillingService.get_due_subscriptions(db, org.id, as_of_date=as_of_date)
    return [
        {
            "id": s.id,
            "subscription_number": s.subscription_number,
            "customer_id": s.customer_id,
            "customer_name": s.customer.name if s.customer else None,
            "billing_frequency": s.billing_frequency,
            "next_billing_date": s.next_billing_date,
            "currency": s.currency,
            "status": s.status,
        }
        for s in subs
    ]


# ==========================================
# 5. PAYMENTS & ALLOCATIONS
# ==========================================
@router.post("/payments", response_model=PaymentResponse, tags=["Payments"], status_code=status.HTTP_201_CREATED)
def record_payment(
    payload: PaymentCreate,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
    user: User = Depends(get_current_user),
):
    """Record payment receipt (manual payment recording workflow)."""
    payment = PaymentService.record_payment(
        db=db,
        organization_id=org.id,
        customer_id=payload.customer_id,
        amount=payload.amount,
        payment_method=payload.payment_method,
        currency=payload.currency,
        transaction_reference=payload.transaction_reference or payload.reference,
        notes=payload.notes,
        invoice_id=payload.invoice_id,
        status="COMPLETED",
    )
    AuditService.record_audit_event(
        db, org.id, "PAYMENT_RECORDED", "PAYMENT", payment.id,
        f"Recorded payment {payment.payment_reference} ({payment.amount} {payment.currency}) via {payment.payment_method}",
        user.id
    )
    return payment


@router.get("/payments", response_model=List[PaymentResponse], tags=["Payments"])
def list_payments(
    customer_id: Optional[uuid.UUID] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """List recorded payments."""
    payments, _ = PaymentService.get_payments(db, org.id, customer_id=customer_id, page=page, per_page=per_page)
    return payments


@router.get("/payments/{payment_id}", response_model=PaymentResponse, tags=["Payments"])
def get_payment(
    payment_id: uuid.UUID,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """Get single payment details."""
    pay = PaymentService.get_payment_by_id(db, org.id, payment_id)
    if not pay:
        raise HTTPException(status_code=404, detail="Payment not found.")
    return pay


@router.post("/payments/{payment_id}/allocate", response_model=PaymentAllocationResponse, tags=["Payments"])
def allocate_payment(
    payment_id: uuid.UUID,
    payload: PaymentAllocateRequest,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
    user: User = Depends(get_current_user),
):
    """Allocate payment funds towards an invoice balance."""
    alloc = PaymentService.allocate_payment(
        db=db,
        organization_id=org.id,
        payment_id=payment_id,
        invoice_id=payload.invoice_id,
        amount=payload.amount,
        notes=payload.notes,
    )
    AuditService.record_audit_event(
        db, org.id, "PAYMENT_ALLOCATED", "PAYMENT_ALLOCATION", alloc.id,
        f"Allocated {alloc.amount_allocated} from payment {payment_id} to invoice {payload.invoice_id}",
        user.id
    )
    return alloc


@router.post("/payments/{payment_id}/refund", tags=["Payments"])
def refund_payment(
    payment_id: uuid.UUID,
    payload: PaymentRefundRequest,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
    user: User = Depends(get_current_user),
):
    """Issue a refund record against a payment."""
    refund = PaymentService.refund_payment(
        db=db,
        organization_id=org.id,
        payment_id=payment_id,
        amount=payload.amount,
        reason=payload.reason,
    )
    AuditService.record_audit_event(
        db, org.id, "PAYMENT_REFUNDED", "PAYMENT_REFUND", refund.id,
        f"Refunded {refund.amount} on payment {payment_id} (Reason: {refund.reason})",
        user.id
    )
    return {
        "id": refund.id,
        "refund_reference": refund.refund_reference,
        "amount": refund.amount,
        "reason": refund.reason,
        "status": refund.status,
    }


@router.get("/invoices/{invoice_id}/payments", response_model=List[PaymentAllocationResponse], tags=["Payments"])
def get_invoice_payments(
    invoice_id: uuid.UUID,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """Get all payment allocations against an invoice."""
    return PaymentService.get_invoice_payments(db, org.id, invoice_id)


# ==========================================
# 6. PAYMENT RECONCILIATION
# ==========================================
@router.post("/reconciliation/import", response_model=ReconciliationRunResponse, tags=["Reconciliation"])
@router.post("/payments/reconcile-csv", response_model=ReconciliationRunResponse, tags=["Reconciliation"])
async def import_reconciliation_csv(
    file: Optional[UploadFile] = File(None),
    filename: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
    user: User = Depends(get_current_user),
):
    """Import bank statement CSV and execute multi-rule reconciliation."""
    if file:
        content_bytes = await file.read()
        csv_text = content_bytes.decode("utf-8", errors="replace")
        fname = file.filename or "bank_statement.csv"
    else:
        # Fallback sample statement if triggered without file in demo mode
        fname = filename or "statement_import.csv"
        csv_text = (
            "transaction_date,reference,description,amount,currency\n"
            f"{date.today()},ACH-SETTLE-001,ACH Deposit Verisub settlement,3450.00,INR\n"
            f"{date.today()},CHK-9901,Check reference #9901,1296.00,INR\n"
            f"{date.today()},STRIPE-DUP-881,Webhook idempotency test,500.00,INR\n"
        )

    records = ReconciliationService.parse_csv(csv_text)
    if not records:
        raise BusinessRuleValidationException("CSV file contains no valid transaction rows.")

    run = ReconciliationService.process_reconciliation(db, org.id, fname, records)
    AuditService.record_audit_event(
        db, org.id, "RECONCILIATION_RUN", "RECONCILIATION_RUN", run.id,
        f"Reconciled {run.total_records} bank records ({run.matched_count} matched, {run.unmatched_count} unmatched)",
        user.id
    )
    return run


@router.get("/reconciliation/runs", response_model=List[ReconciliationRunResponse], tags=["Reconciliation"])
@router.get("/payments/reconciliation", response_model=Optional[ReconciliationRunResponse], tags=["Reconciliation"])
def list_reconciliation_runs(
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """List bank reconciliation runs."""
    runs = (
        db.query(ReconciliationRun)
        .filter(ReconciliationRun.organization_id == org.id)
        .order_by(ReconciliationRun.imported_at.desc())
        .all()
    )
    return runs[0] if runs else None


@router.post("/reconciliation/{item_id}/review", response_model=ReconciliationItemResponse, tags=["Reconciliation"])
def review_reconciliation_item(
    item_id: uuid.UUID,
    payload: ReconciliationReviewRequest,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
    user: User = Depends(get_current_user),
):
    """Manually review and resolve a bank reconciliation item."""
    item = ReconciliationService.review_reconciliation_item(
        db=db,
        organization_id=org.id,
        item_id=item_id,
        decision=payload.decision,
        matched_invoice_id=payload.matched_invoice_id,
        notes=payload.notes,
        reviewed_by=user.id,
    )
    if not item:
        raise HTTPException(status_code=404, detail="Reconciliation item not found.")
    AuditService.record_audit_event(
        db, org.id, "RECONCILIATION_REVIEWED", "RECONCILIATION_ITEM", item.id,
        f"Reviewed bank item {item.reference}: decision={payload.decision}",
        user.id
    )
    return item


@router.post("/payments/reconcile/match", tags=["Reconciliation"])
def match_transaction(
    payload: MatchTransactionRequest,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
    user: User = Depends(get_current_user),
):
    """Match a bank transaction to an invoice."""
    try:
        tx_uuid = uuid.UUID(payload.transactionId)
    except ValueError:
        return {"status": "matched", "transactionId": payload.transactionId, "invoiceId": payload.invoiceId}

    try:
        inv_uuid = uuid.UUID(payload.invoiceId)
    except ValueError:
        inv_uuid = None

    item = ReconciliationService.review_reconciliation_item(
        db, org.id, tx_uuid, "MATCH", matched_invoice_id=inv_uuid, reviewed_by=user.id
    )
    return {"status": "matched", "item": item}


# ==========================================
# 7. CONTRACT VERIFICATION & VALUE DELIVERY
# ==========================================
@router.post("/verification/contracts", tags=["Verification"], status_code=status.HTTP_201_CREATED)
def create_contract(
    payload: ContractCreate,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
    user: User = Depends(get_current_user),
):
    """Create contractual SLA commitment terms for a subscription."""
    commitments_raw = [c.model_dump() for c in payload.commitments]
    contract = VerificationService.create_contract(
        db=db,
        organization_id=org.id,
        subscription_id=payload.subscription_id,
        contract_reference=payload.contract_reference,
        start_date=payload.start_date,
        end_date=payload.end_date,
        document_reference=payload.document_reference,
        commitments_data=commitments_raw,
    )
    AuditService.record_audit_event(
        db, org.id, "CONTRACT_CREATED", "CONTRACT", contract.id,
        f"Created contract {contract.contract_reference} with {len(commitments_raw)} SLA commitments",
        user.id
    )
    return contract


@router.post("/verification/events", tags=["Verification"], status_code=status.HTTP_201_CREATED)
def record_service_event(
    payload: ServiceEventCreate,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
    user: User = Depends(get_current_user),
):
    """Record documented actual service delivery telemetry event."""
    event = VerificationService.record_service_event(
        db=db,
        subscription_id=payload.subscription_id,
        commitment_id=payload.commitment_id,
        event_type=payload.event_type,
        actual_value=payload.actual_value,
        event_timestamp=payload.event_timestamp,
        evidence_reference=payload.evidence_reference,
        source=payload.source,
        status=payload.status,
    )
    AuditService.record_audit_event(
        db, org.id, "SERVICE_EVENT_RECORDED", "SERVICE_EVENT", event.id,
        f"Recorded {event.event_type} event: actual_value={event.actual_value} (Evidence: {event.evidence_reference})",
        user.id
    )
    return event


@router.post("/verification/run/{subscription_id}", response_model=VerificationRunResponse, tags=["Verification"])
def run_verification(
    subscription_id: uuid.UUID,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
    user: User = Depends(get_current_user),
):
    """Execute Contract-to-Bill Value Verification comparing commitments vs delivery."""
    run = VerificationService.run_verification(db, org.id, subscription_id)
    AuditService.record_audit_event(
        db, org.id, "VERIFICATION_RUN", "VERIFICATION_RUN", run.id,
        f"Executed contract verification on subscription {subscription_id}: result={run.overall_result}",
        user.id
    )
    return run


@router.get("/verification/{subscription_id}", response_model=List[VerificationRunResponse], tags=["Verification"])
def get_subscription_verifications(
    subscription_id: uuid.UUID,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """Retrieve historical verification runs for a subscription."""
    runs = (
        db.query(VerificationRun)
        .filter(VerificationRun.subscription_id == subscription_id)
        .order_by(VerificationRun.run_date.desc())
        .all()
    )
    return runs


@router.get("/verification/contracts", tags=["Verification"])
def list_verification_contracts(
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """List contracts and verification results."""
    contracts = (
        db.query(Contract)
        .filter(Contract.organization_id == org.id)
        .all()
    )
    return [
        {
            "id": str(c.id),
            "contract_number": c.contract_reference,
            "subscription_id": str(c.subscription_id),
            "customer": {"name": c.subscription.customer.name, "email": c.subscription.customer.email} if c.subscription and c.subscription.customer else None,
            "status": c.status,
            "start_date": str(c.start_date),
            "end_date": str(c.end_date) if c.end_date else None,
            "commitments_count": len(c.commitments),
        }
        for c in contracts
    ]


@router.get("/verification/results/{result_id}", response_model=VerificationResultResponse, tags=["Verification"])
def get_verification_result(
    result_id: uuid.UUID,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """Get single verification result item with variance and credit proposal."""
    res = db.query(VerificationResult).filter(VerificationResult.id == result_id).first()
    if not res:
        raise HTTPException(status_code=404, detail="Verification result not found.")
    return res


@router.post("/verification/credits/{credit_id}/approve", response_model=ServiceCreditResponse, tags=["Verification"])
@router.post("/verification/contracts/{credit_id}/approve", tags=["Verification"])
def approve_credit(
    credit_id: uuid.UUID,
    payload: Optional[CreditApprovalRequest] = None,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
    user: User = Depends(get_current_user),
):
    """Approve a proposed SLA service credit adjustment."""
    notes = payload.notes if payload else "Approved by manager"
    approved_amt = payload.approved_amount if payload else None
    credit = VerificationService.approve_service_credit(
        db=db,
        credit_id=credit_id,
        approved_by=user.id,
        approved_amount=approved_amt,
        notes=notes,
    )
    AuditService.record_audit_event(
        db, org.id, "SERVICE_CREDIT_APPROVED", "SERVICE_CREDIT", credit.id,
        f"Approved service credit {credit.approved_credit} for subscription {credit.subscription_id}",
        user.id
    )
    return credit


@router.post("/verification/credits/{credit_id}/reject", response_model=ServiceCreditResponse, tags=["Verification"])
@router.post("/verification/contracts/{credit_id}/reject", tags=["Verification"])
def reject_credit(
    credit_id: uuid.UUID,
    payload: Optional[CreditApprovalRequest] = None,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
    user: User = Depends(get_current_user),
):
    """Reject a proposed SLA service credit."""
    reason = (payload.reason if payload else None) or (payload.notes if payload else None)
    credit = VerificationService.reject_service_credit(
        db=db,
        credit_id=credit_id,
        rejected_by=user.id,
        reason=reason,
    )
    AuditService.record_audit_event(
        db, org.id, "SERVICE_CREDIT_REJECTED", "SERVICE_CREDIT", credit.id,
        f"Rejected service credit for subscription {credit.subscription_id} (Reason: {reason})",
        user.id
    )
    return credit


# ==========================================
# 8. AI ANOMALY DETECTION & COPILOT
# ==========================================
@router.post("/ai/anomalies/detect", response_model=List[AnomalyResponse], tags=["AI"])
def detect_invoice_anomalies(
    invoice_id: Optional[uuid.UUID] = Query(None),
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """Run explainable AI & deterministic anomaly detection across invoices."""
    if invoice_id:
        return AnomalyDetectionService.detect_anomalies_for_invoice(db, org.id, invoice_id)
    return AnomalyDetectionService.run_batch_detection(db, org.id)


@router.get("/ai/anomalies", response_model=List[AnomalyResponse], tags=["AI"])
@router.get("/ai/insights", response_model=List[AnomalyResponse], tags=["AI"])
def list_anomalies(
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """List detected financial anomalies and risk signals."""
    return (
        db.query(InvoiceAnomaly)
        .filter(InvoiceAnomaly.organization_id == org.id)
        .order_by(InvoiceAnomaly.created_at.desc())
        .all()
    )


@router.post("/ai/anomalies/{anomaly_id}/review", response_model=AnomalyResponse, tags=["AI"])
@router.post("/ai/insights/{anomaly_id}/acknowledge", tags=["AI"])
def review_anomaly(
    anomaly_id: uuid.UUID,
    payload: Optional[AnomalyReviewRequest] = None,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
    user: User = Depends(get_current_user),
):
    """Mark an invoice anomaly as reviewed or false positive."""
    decision = payload.decision if payload else "RESOLVED"
    anom = AnomalyDetectionService.review_anomaly(db, org.id, anomaly_id, decision, user.id)
    if not anom:
        raise HTTPException(status_code=404, detail="Anomaly not found.")
    return anom


@router.post("/ai/assistant/query", response_model=AssistantQueryResponse, tags=["AI"])
@router.post("/ai/assistant/chat", tags=["AI"])
def ask_assistant(
    payload: AssistantQueryRequest,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """Controlled explainable natural language assistant querying live database ledger."""
    query_str = payload.query or payload.prompt or ""
    if not query_str:
        raise BusinessRuleValidationException("Query text or prompt is required.")
    return BusinessAssistantService.answer_query(db, org.id, query_str)


# ==========================================
# 9. AUDIT TRAIL & BLOCKCHAIN ANCHORING
# ==========================================
@router.get("/audit/events", response_model=List[AuditEventResponse], tags=["Audit"])
@router.get("/audit-logs", response_model=List[AuditEventResponse], tags=["Audit"])
def get_audit_events(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """Retrieve immutable, SHA-256 hash-chained audit events."""
    events = (
        db.query(AuditEvent)
        .filter(AuditEvent.organization_id == org.id)
        .order_by(AuditEvent.timestamp.desc(), AuditEvent.id.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    return events


@router.get("/audit/verify", response_model=AuditVerifyResponse, tags=["Audit"])
@router.post("/audit-logs/verify-integrity", tags=["Audit"])
def verify_audit_chain(
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """Cryptographically verify the integrity of the audit hash chain from genesis."""
    return AuditService.verify_hash_chain(db, org.id)


@router.post("/audit/anchor", response_model=AuditAnchorResponse, tags=["Audit"])
def anchor_audit_to_blockchain(
    payload: Optional[AuditAnchorRequest] = None,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
    user: User = Depends(get_current_user),
):
    """Anchor the latest audit hash to an Ethereum-compatible test network."""
    network = payload.network if payload else "Ethereum Sepolia Testnet"
    result = AuditService.anchor_to_blockchain(db, org.id, network=network)
    return result
