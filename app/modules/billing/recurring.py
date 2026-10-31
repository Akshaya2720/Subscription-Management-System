import uuid
from datetime import date, datetime, timezone, timedelta
from dateutil.relativedelta import relativedelta
from decimal import Decimal
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_, exc

from app.modules.subscriptions.models import Subscription, SubscriptionItem
from app.modules.billing.models import (
    BillingRun,
    BillingRunItem,
    Invoice,
    InvoiceItem,
    TaxRule,
)
from app.modules.billing.invoices import InvoiceService
from app.modules.billing.taxes import TaxService


class RecurringBillingService:
    @staticmethod
    def calculate_billing_period(start_date: date, frequency: str) -> Tuple[date, date, date]:
        """
        Calculate (period_start, period_end, next_billing_date) based on cadence.
        Cadences supported: DAILY, WEEKLY, MONTHLY, YEARLY.
        """
        freq = frequency.upper()
        period_start = start_date

        if freq == "DAILY":
            period_end = period_start + timedelta(days=1)
            next_date = period_end
        elif freq == "WEEKLY":
            period_end = period_start + timedelta(days=7)
            next_date = period_end
        elif freq == "MONTHLY":
            period_end = period_start + relativedelta(months=1)
            next_date = period_end
        elif freq == "YEARLY":
            period_end = period_start + relativedelta(years=1)
            next_date = period_end
        else:
            # Default monthly
            period_end = period_start + relativedelta(months=1)
            next_date = period_end

        return period_start, period_end, next_date

    @staticmethod
    def get_due_subscriptions(
        db: Session,
        organization_id: uuid.UUID,
        as_of_date: Optional[date] = None,
    ) -> List[Subscription]:
        """
        Retrieve billable subscriptions:
        - Must be ACTIVE.
        - Must be due: next_billing_date <= as_of_date.
        - Must not be expired: expiry_date is null OR expiry_date >= next_billing_date.
        - Filtered by organization_id.
        """
        target_date = as_of_date or date.today()
        query = (
            db.query(Subscription)
            .filter(
                Subscription.organization_id == organization_id,
                Subscription.status == "ACTIVE",
                Subscription.next_billing_date <= target_date,
                or_(
                    Subscription.expiry_date == None,
                    Subscription.expiry_date >= Subscription.next_billing_date,
                ),
            )
            .order_by(Subscription.next_billing_date.asc())
        )
        return query.all()

    @staticmethod
    def execute_billing_run(
        db: Session,
        organization_id: uuid.UUID,
        as_of_date: Optional[date] = None,
    ) -> BillingRun:
        """
        Execute deterministic automated recurring billing run.
        - Finds due subscriptions.
        - Generates invoice with line items from subscription snapshot.
        - Idempotent against duplicate period billing.
        - Updates next_billing_date only after successful commit.
        """
        target_date = as_of_date or date.today()
        started_at = datetime.now(timezone.utc)
        run_ref = f"RUN-{started_at.strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"

        billing_run = BillingRun(
            id=uuid.uuid4(),
            organization_id=organization_id,
            run_reference=run_ref,
            started_at=started_at,
            status="RUNNING",
            total_processed=0,
            successful_count=0,
            failed_count=0,
            logs=[
                f"[{started_at.strftime('%H:%M:%S')}] Started recurring billing run {run_ref} for organization {organization_id}.",
                f"[{started_at.strftime('%H:%M:%S')}] Scanning subscriptions due on or before {target_date}.",
            ],
            created_at=started_at,
        )
        db.add(billing_run)
        db.commit()
        db.refresh(billing_run)

        due_subs = RecurringBillingService.get_due_subscriptions(
            db, organization_id, target_date
        )
        billing_run.total_processed = len(due_subs)

        successful = 0
        failed = 0

        # Fetch active tax rules for the organization once
        active_tax_rules = TaxService.get_tax_rules(db, organization_id, active_only=True)

        for sub in due_subs:
            period_start, period_end, next_billing_date = (
                RecurringBillingService.calculate_billing_period(
                    sub.next_billing_date, sub.billing_frequency
                )
            )

            # Check if invoice for this period already exists (Idempotency check)
            existing_invoice = (
                db.query(Invoice)
                .filter(
                    Invoice.organization_id == organization_id,
                    Invoice.subscription_id == sub.id,
                    Invoice.billing_period_start == period_start,
                    Invoice.billing_period_end == period_end,
                    Invoice.invoice_type == "RECURRING",
                )
                .first()
            )

            if existing_invoice:
                # Duplicate detected: skip and advance next_billing_date to prevent stalling
                item_record = BillingRunItem(
                    id=uuid.uuid4(),
                    billing_run_id=billing_run.id,
                    subscription_id=sub.id,
                    invoice_id=existing_invoice.id,
                    status="SKIPPED",
                    error_message=f"Invoice for period {period_start} to {period_end} already exists ({existing_invoice.invoice_number}).",
                    created_at=datetime.now(timezone.utc),
                )
                db.add(item_record)
                sub.next_billing_date = next_billing_date
                db.commit()
                continue

            try:
                # Generate invoice
                sub_items = (
                    db.query(SubscriptionItem)
                    .filter(SubscriptionItem.subscription_id == sub.id)
                    .all()
                )
                if not sub_items:
                    raise ValueError(f"Subscription {sub.subscription_number} has no active items.")

                items_payload = []
                for sit in sub_items:
                    items_payload.append({
                        "product_id": sit.product_id,
                        "variant_id": sit.variant_id,
                        "description_snapshot": sit.description_snapshot,
                        "quantity": sit.quantity,
                        "unit_price": sit.unit_price_snapshot,
                    })

                due_date = period_start + timedelta(days=15)
                # Payment terms parsing (e.g. NET_30)
                if sub.payment_terms == "NET_30":
                    due_date = period_start + timedelta(days=30)
                elif sub.payment_terms == "NET_15":
                    due_date = period_start + timedelta(days=15)
                elif sub.payment_terms == "DUE_ON_RECEIPT":
                    due_date = period_start

                invoice = InvoiceService.create_invoice(
                    db=db,
                    organization_id=organization_id,
                    customer_id=sub.customer_id,
                    subscription_id=sub.id,
                    due_date=due_date,
                    items_data=items_payload,
                    billing_period_start=period_start,
                    billing_period_end=period_end,
                    currency=sub.currency,
                    invoice_type="RECURRING",
                    notes=f"Recurring billing for {sub.subscription_number} ({sub.billing_frequency})",
                    status="CONFIRMED",  # Confirmed on recurring generation
                )

                # Advance next_billing_date ONLY AFTER successful invoice creation
                sub.next_billing_date = next_billing_date

                # Record success item
                item_record = BillingRunItem(
                    id=uuid.uuid4(),
                    billing_run_id=billing_run.id,
                    subscription_id=sub.id,
                    invoice_id=invoice.id,
                    status="SUCCESS",
                    created_at=datetime.now(timezone.utc),
                )
                db.add(item_record)
                db.commit()
                successful += 1

            except Exception as e:
                db.rollback()
                failed += 1
                error_msg = str(e)
                # Log failure
                item_record = BillingRunItem(
                    id=uuid.uuid4(),
                    billing_run_id=billing_run.id,
                    subscription_id=sub.id,
                    invoice_id=None,
                    status="FAILED",
                    error_message=error_msg,
                    created_at=datetime.now(timezone.utc),
                )
                db.add(item_record)
                db.commit()

        # Finalize run status
        completed_at = datetime.now(timezone.utc)
        billing_run.completed_at = completed_at
        billing_run.successful_count = successful
        billing_run.failed_count = failed

        if failed == 0:
            billing_run.status = "COMPLETED"
        elif successful == 0 and failed > 0:
            billing_run.status = "FAILED"
        else:
            billing_run.status = "COMPLETED_WITH_ERRORS"

        logs = list(billing_run.logs or [])
        logs.append(
            f"[{completed_at.strftime('%H:%M:%S')}] Completed with {successful} successful and {failed} failed subscriptions."
        )
        billing_run.logs = logs

        db.commit()
        db.refresh(billing_run)
        return billing_run

    @staticmethod
    def get_billing_runs(
        db: Session,
        organization_id: uuid.UUID,
        page: int = 1,
        per_page: int = 50,
    ) -> Tuple[List[BillingRun], int]:
        query = db.query(BillingRun).filter(BillingRun.organization_id == organization_id)
        total = query.count()
        runs = (
            query.order_by(BillingRun.started_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        return runs, total

    @staticmethod
    def get_billing_run_by_id(
        db: Session, organization_id: uuid.UUID, run_id: uuid.UUID
    ) -> Optional[BillingRun]:
        return (
            db.query(BillingRun)
            .filter(BillingRun.id == run_id, BillingRun.organization_id == organization_id)
            .first()
        )
