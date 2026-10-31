"""Service layer for Tax Engine, Discount Engine, Invoicing, Simulated Gateway, and Recurring Billing."""

import uuid
import random
from decimal import Decimal, ROUND_HALF_UP
from datetime import date, datetime, timedelta, timezone
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session

from app.core.exceptions import (
    EntityNotFoundException,
    DuplicateEntityException,
    InvalidStateTransitionException,
    BusinessRuleValidationException,
)
from app.models.billing import (
    TaxRule,
    Discount,
    Invoice,
    InvoiceItem,
    Payment,
    InvoiceStatus,
    PaymentMethod,
    DiscountType,
)
from app.models.subscription import Subscription
from app.modules.customers.service import CustomerService
from app.modules.plans.service import PlanService
from app.modules.billing.repository import (
    TaxRuleRepository,
    DiscountRepository,
    InvoiceRepository,
    PaymentRepository,
)
from app.modules.billing.schemas import (
    TaxRuleCreate,
    TaxRuleUpdate,
    DiscountCreate,
    DiscountUpdate,
    InvoiceCreate,
    InvoiceUpdate,
    PaymentCreate,
    PaymentReceipt,
    BillingRunRequest,
    BillingRunResponse,
)


def _round_currency(val: Decimal) -> Decimal:
    return val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class TaxEngine:
    @staticmethod
    def calculate_tax(
        db: Session,
        org_id: uuid.UUID,
        subtotal: Decimal,
        country: Optional[str] = None,
        state_province: Optional[str] = None,
        tax_code: Optional[str] = None,
    ) -> Tuple[Decimal, Decimal, str]:
        """
        Determines applicable tax rate and calculates tax amount.
        Returns: (tax_percent, tax_amount, applied_tax_code)
        """
        repo = TaxRuleRepository(db)
        rule = None

        if tax_code:
            rule = repo.get_by_code(org_id, tax_code)
        if not rule:
            rule = repo.get_default_or_matching(org_id, country=country, state_province=state_province)

        if not rule:
            return Decimal("0.00"), Decimal("0.00"), "NO_TAX"

        tax_percent = rule.rate_percent
        tax_amount = _round_currency(subtotal * (tax_percent / Decimal("100.00")))
        return tax_percent, tax_amount, rule.tax_code


class DiscountEngine:
    @staticmethod
    def apply_discount(
        db: Session,
        org_id: uuid.UUID,
        discount_code: str,
        subtotal: Decimal,
        total_quantity: int = 1,
        target_date: Optional[date] = None,
    ) -> Tuple[Discount, Decimal]:
        """
        Validates discount eligibility (dates, usage limits, min purchase/quantity)
        and computes discount amount.
        """
        repo = DiscountRepository(db)
        discount = repo.get_by_code(org_id, discount_code)
        if not discount or not discount.is_active:
            raise BusinessRuleValidationException(f"Discount code '{discount_code}' is invalid or inactive.")

        check_date = target_date or date.today()
        if discount.start_date and check_date < discount.start_date:
            raise BusinessRuleValidationException(f"Discount code '{discount_code}' is not yet active.")
        if discount.end_date and check_date > discount.end_date:
            raise BusinessRuleValidationException(f"Discount code '{discount_code}' has expired.")

        if discount.max_uses is not None and discount.times_used >= discount.max_uses:
            raise BusinessRuleValidationException(f"Discount code '{discount_code}' has reached its maximum usage limit.")

        if subtotal < discount.min_purchase_amount:
            raise BusinessRuleValidationException(
                f"Discount code '{discount_code}' requires a minimum purchase amount of {discount.min_purchase_amount}."
            )

        if total_quantity < discount.min_quantity:
            raise BusinessRuleValidationException(
                f"Discount code '{discount_code}' requires a minimum quantity of {discount.min_quantity}."
            )

        # Compute discount amount
        if discount.discount_type == DiscountType.PERCENTAGE:
            calc_amount = _round_currency(subtotal * (discount.amount / Decimal("100.00")))
        else:
            calc_amount = discount.amount

        # Cap discount so subtotal doesn't become negative
        final_discount = min(calc_amount, subtotal)
        return discount, final_discount


class BillingService:
    def __init__(self, db: Session):
        self.db = db
        self.tax_repo = TaxRuleRepository(db)
        self.discount_repo = DiscountRepository(db)
        self.invoice_repo = InvoiceRepository(db)
        self.payment_repo = PaymentRepository(db)

    @staticmethod
    def _generate_invoice_number() -> str:
        today_str = datetime.now().strftime("%Y%m%d")
        rand_num = random.randint(1000, 9999)
        return f"INV-{today_str}-{rand_num}"

    # ── Tax Rules CRUD ────────────────────────────────────────────────────────

    def create_tax_rule(self, org_id: uuid.UUID, data: TaxRuleCreate) -> TaxRule:
        if self.tax_repo.get_by_code(org_id, data.tax_code):
            raise DuplicateEntityException(f"Tax rule with code '{data.tax_code}' already exists.")
        rule = TaxRule(
            organization_id=org_id,
            name=data.name,
            tax_type=data.tax_code,
            rate_percentage=data.rate_percent,
            country_code=data.country or "US",
            state_or_province=data.state_province,
            is_default=data.is_default,
            is_active=data.is_active,
        )
        return self.tax_repo.save(rule)

    def list_tax_rules(self, org_id: uuid.UUID) -> List[TaxRule]:
        return self.tax_repo.list(org_id)

    # ── Discounts CRUD ────────────────────────────────────────────────────────

    def create_discount(self, org_id: uuid.UUID, data: DiscountCreate) -> Discount:
        if self.discount_repo.get_by_code(org_id, data.code):
            raise DuplicateEntityException(f"Discount with code '{data.code}' already exists.")
        discount = Discount(
            organization_id=org_id,
            code=data.code.upper(),
            description=data.description or data.code,
            discount_type=data.discount_type.value if hasattr(data.discount_type, "value") else str(data.discount_type),
            amount=data.amount,
            min_purchase_amount=data.min_purchase_amount or Decimal("0.00"),
            min_quantity=data.min_quantity or 1,
            max_uses=data.max_uses,
            start_date=data.start_date or date.today(),
            end_date=data.end_date,
            product_id=data.product_id,
            applies_to_subscription=True if not data.product_id else False,
            is_active=data.is_active,
        )
        return self.discount_repo.save(discount)

    def list_discounts(self, org_id: uuid.UUID) -> List[Discount]:
        return self.discount_repo.list(org_id)

    # ── Invoicing ─────────────────────────────────────────────────────────────

    def create_invoice(self, org_id: uuid.UUID, data: InvoiceCreate) -> Invoice:
        customer = CustomerService.get_customer(self.db, org_id, data.customer_id)
        invoice_number = self._generate_invoice_number()

        # Calculate line items
        subtotal = Decimal("0.00")
        total_qty = 0
        line_objects: List[InvoiceItem] = []

        for item_data in data.items:
            line_subtotal = _round_currency(item_data.unit_price * Decimal(item_data.quantity))
            line_tax = _round_currency(line_subtotal * (item_data.tax_percent / Decimal("100.00")))
            line_total = _round_currency(line_subtotal + line_tax - item_data.discount_amount)
            subtotal += line_subtotal
            total_qty += item_data.quantity

            line_objects.append(
                InvoiceItem(
                    description=item_data.description,
                    quantity=item_data.quantity,
                    unit_price=item_data.unit_price,
                    line_total=line_total,
                )
            )

        # Apply overall discount if provided
        discount_amount = Decimal("0.00")
        if data.discount_code:
            discount_obj, discount_amount = DiscountEngine.apply_discount(
                self.db, org_id, data.discount_code, subtotal, total_quantity=total_qty, target_date=data.issue_date
            )
            self.discount_repo.increment_usage(discount_obj)

        # Calculate taxes on discounted subtotal
        taxable_amount = max(Decimal("0.00"), subtotal - discount_amount)
        tax_percent, tax_amount, _ = TaxEngine.calculate_tax(
            self.db, org_id, taxable_amount, country="US"
        )

        total_amount = _round_currency(taxable_amount + tax_amount)

        invoice = Invoice(
            organization_id=org_id,
            customer_id=customer.id,
            subscription_id=data.subscription_id,
            invoice_number=invoice_number,
            status=InvoiceStatus.DRAFT,
            issue_date=data.issue_date,
            due_date=data.due_date,
            period_start=data.period_start,
            period_end=data.period_end,
            currency=data.currency,
            subtotal=subtotal,
            discount_amount=discount_amount,
            tax_amount=tax_amount,
            sla_credit_amount=Decimal("0.00"),
            total_amount=total_amount,
            amount_paid=Decimal("0.00"),
            amount_due=total_amount,
            notes=data.notes,
        )
        self.db.add(invoice)
        self.db.flush()

        for item in line_objects:
            item.invoice_id = invoice.id
            self.db.add(item)

        self.invoice_repo.log_status_change(invoice.id, "NONE", InvoiceStatus.DRAFT.value, "Invoice created.")
        self.db.commit()
        self.db.refresh(invoice)
        return invoice

    def confirm_invoice(self, org_id: uuid.UUID, invoice_id: uuid.UUID) -> Invoice:
        invoice = self.invoice_repo.get_by_id(org_id, invoice_id)
        if not invoice:
            raise EntityNotFoundException("Invoice", str(invoice_id))

        curr_status = invoice.status.value if hasattr(invoice.status, "value") else str(invoice.status)
        if curr_status != InvoiceStatus.DRAFT.value:
            raise InvalidStateTransitionException(curr_status, InvoiceStatus.CONFIRMED.value, "Only DRAFT can be confirmed.")

        invoice.status = InvoiceStatus.CONFIRMED.value
        self.invoice_repo.log_status_change(invoice.id, curr_status, InvoiceStatus.CONFIRMED.value, "Invoice confirmed.")
        self.db.commit()
        self.db.refresh(invoice)
        return invoice

    def cancel_invoice(self, org_id: uuid.UUID, invoice_id: uuid.UUID) -> Invoice:
        invoice = self.invoice_repo.get_by_id(org_id, invoice_id)
        if not invoice:
            raise EntityNotFoundException("Invoice", str(invoice_id))

        curr_status = invoice.status.value if hasattr(invoice.status, "value") else str(invoice.status)
        if curr_status == InvoiceStatus.PAID.value:
            raise InvalidStateTransitionException(curr_status, InvoiceStatus.CANCELLED.value, "Cannot cancel PAID invoice.")

        invoice.status = InvoiceStatus.CANCELLED.value
        self.invoice_repo.log_status_change(invoice.id, curr_status, InvoiceStatus.CANCELLED.value, "Invoice cancelled.")
        self.db.commit()
        self.db.refresh(invoice)
        return invoice

    # ── Simulated Payment Gateway ─────────────────────────────────────────────

    def record_payment(self, org_id: uuid.UUID, invoice_id: uuid.UUID, data: PaymentCreate) -> PaymentReceipt:
        invoice = self.invoice_repo.get_by_id(org_id, invoice_id)
        if not invoice:
            raise EntityNotFoundException("Invoice", str(invoice_id))

        curr_status = invoice.status.value if hasattr(invoice.status, "value") else str(invoice.status)
        if curr_status in (InvoiceStatus.CANCELLED.value, InvoiceStatus.DRAFT.value):
            raise BusinessRuleValidationException(f"Cannot record payment for invoice in '{curr_status}' status. Please confirm invoice first.")

        if data.amount <= Decimal("0.00"):
            raise BusinessRuleValidationException("Payment amount must be greater than 0.")

        if data.amount > invoice.amount_due:
            raise BusinessRuleValidationException(
                f"Payment amount ({data.amount}) exceeds outstanding balance ({invoice.amount_due}). Overpayment is rejected."
            )

        method_str = data.payment_method.value if hasattr(data.payment_method, "value") else str(data.payment_method)
        gateway_txn_id = f"SIM-TXN-{uuid.uuid4().hex[:12].upper()}"
        payment = Payment(
            organization_id=org_id,
            invoice_id=invoice.id,
            amount=data.amount,
            payment_method=method_str,
            payment_date=datetime.now(timezone.utc),
            status="COMPLETED",
            transaction_reference=data.reference or gateway_txn_id,
            notes=data.notes,
        )
        self.db.add(payment)
        self.db.flush()

        # Update invoice balances
        invoice.amount_paid = _round_currency(invoice.amount_paid + data.amount)
        invoice.amount_due = _round_currency(invoice.amount_due - data.amount)

        if invoice.amount_due <= Decimal("0.00"):
            invoice.status = InvoiceStatus.PAID.value
            self.invoice_repo.log_status_change(invoice.id, curr_status, InvoiceStatus.PAID.value, "Paid in full.")

        self.db.commit()
        self.db.refresh(invoice)

        return PaymentReceipt(
            receipt_id=f"RCPT-{uuid.uuid4().hex[:8].upper()}",
            payment_id=payment.id,
            invoice_id=invoice.id,
            invoice_number=invoice.invoice_number,
            amount_paid=data.amount,
            remaining_balance=invoice.amount_due,
            payment_method=method_str,
            timestamp=datetime.now(timezone.utc),
            status="SUCCESS",
            message="Payment recorded successfully via simulated gateway.",
        )

    # ── Automated Recurring Billing Run ───────────────────────────────────────

    def run_recurring_billing(self, org_id: uuid.UUID, req: BillingRunRequest) -> BillingRunResponse:
        """
        Idempotent recurring billing engine:
        - Scans active subscriptions due on or before run_date.
        - Calculates billing period (period_start, period_end).
        - Idempotency guard: checks if invoice exists for (subscription_id, period_start, period_end).
        - Creates line items, applies taxes and discounts.
        - Checks plan configuration: is_auto_close_at_end.
        - Advances next_billing_date or closes subscription.
        """
        run_date = req.run_date
        due_subscriptions = (
            self.db.query(Subscription)
            .filter(
                Subscription.organization_id == org_id,
                Subscription.status == "ACTIVE",
                Subscription.next_billing_date <= run_date,
            )
            .all()
        )

        invoices_created = 0
        invoices_skipped = 0
        total_billed = Decimal("0.00")
        created_ids: List[uuid.UUID] = []

        for sub in due_subscriptions:
            period_start = sub.next_billing_date
            # Calculate period_end based on frequency
            freq = sub.billing_frequency.upper()
            if freq == "DAILY":
                period_end = period_start + timedelta(days=1)
                next_date = period_end
            elif freq == "WEEKLY":
                period_end = period_start + timedelta(weeks=1)
                next_date = period_end
            elif freq == "YEARLY":
                period_end = period_start + timedelta(days=365)
                next_date = period_end
            else:  # MONTHLY
                period_end = period_start + timedelta(days=30)
                next_date = period_end

            # Idempotency check: unique constraint (subscription_id, period_start, period_end)
            existing_invoice = self.invoice_repo.get_by_subscription_and_period(
                subscription_id=sub.id, period_start=period_start, period_end=period_end
            )
            if existing_invoice:
                invoices_skipped += 1
                continue

            # Compute lines
            subtotal = Decimal("0.00")
            line_items: List[InvoiceItem] = []
            for s_item in sub.items:
                unit_p = s_item.unit_price_snapshot if hasattr(s_item, "unit_price_snapshot") else Decimal(str(getattr(s_item, "unit_price", "0.00")))
                desc = s_item.description_snapshot if hasattr(s_item, "description_snapshot") else str(getattr(s_item, "description", "Subscription Item"))
                line_sub = _round_currency(unit_p * Decimal(s_item.quantity))
                subtotal += line_sub

                line_items.append(
                    InvoiceItem(
                        description=desc,
                        quantity=s_item.quantity,
                        unit_price=unit_p,
                        line_total=line_sub,
                    )
                )

            # Apply tax rule
            tax_percent, tax_amount, _ = TaxEngine.calculate_tax(self.db, org_id, subtotal)
            total_amount = _round_currency(subtotal + tax_amount)

            due_date = period_start + timedelta(days=14)
            inv = Invoice(
                organization_id=org_id,
                customer_id=sub.customer_id,
                subscription_id=sub.id,
                invoice_number=self._generate_invoice_number(),
                status=InvoiceStatus.CONFIRMED if req.auto_confirm else InvoiceStatus.DRAFT,
                issue_date=run_date,
                due_date=due_date,
                period_start=period_start,
                period_end=period_end,
                currency=sub.currency or "USD",
                subtotal=subtotal,
                discount_amount=Decimal("0.00"),
                tax_amount=tax_amount,
                sla_credit_amount=Decimal("0.00"),
                total_amount=total_amount,
                amount_paid=Decimal("0.00"),
                amount_due=total_amount,
                notes=f"Automated recurring bill for subscription {sub.subscription_number} ({period_start} to {period_end}).",
            )
            self.db.add(inv)
            self.db.flush()

            for item in line_items:
                item.invoice_id = inv.id
                self.db.add(item)

            self.invoice_repo.log_status_change(inv.id, "NONE", inv.status.value, "Automated recurring billing run.")

            # Update subscription lifecycle
            plan = PlanService.get_plan(self.db, org_id, sub.plan_id)
            if plan.is_auto_close_at_end and sub.end_date and period_end >= sub.end_date:
                sub.status = "CLOSED"
            else:
                sub.next_billing_date = next_date

            invoices_created += 1
            total_billed += total_amount
            created_ids.append(inv.id)

        self.db.commit()

        return BillingRunResponse(
            run_date=run_date,
            subscriptions_scanned=len(due_subscriptions),
            invoices_created=invoices_created,
            invoices_skipped=invoices_skipped,
            total_billed_amount=total_billed,
            created_invoice_ids=created_ids,
        )
