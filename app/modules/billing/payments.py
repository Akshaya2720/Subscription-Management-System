import uuid
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_, func

from app.core.exceptions import (
    EntityNotFoundException,
    InvalidStateTransitionException,
    BusinessRuleValidationException,
)
from app.modules.billing.models import (
    Payment,
    PaymentAllocation,
    PaymentRefund,
    Invoice,
)
from app.modules.customers.models import Customer


class PaymentService:
    @staticmethod
    def generate_payment_reference() -> str:
        return f"PAY-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

    @staticmethod
    def record_payment(
        db: Session,
        organization_id: uuid.UUID,
        customer_id: Optional[uuid.UUID],
        amount: Decimal,
        payment_method: str = "BANK_TRANSFER",
        currency: str = "INR",
        transaction_reference: Optional[str] = None,
        notes: Optional[str] = None,
        invoice_id: Optional[uuid.UUID] = None,
        status: str = "COMPLETED",
    ) -> Payment:
        """
        Record a payment (manual recording workflow).
        If invoice_id is supplied, automatically allocate to that invoice up to its due balance.
        """
        if amount <= Decimal("0.00"):
            raise BusinessRuleValidationException("Payment amount must be greater than zero.")

        # If invoice_id provided, infer customer if missing
        if invoice_id and not customer_id:
            inv = (
                db.query(Invoice)
                .filter(Invoice.id == invoice_id, Invoice.organization_id == organization_id)
                .first()
            )
            if inv:
                customer_id = inv.customer_id
                currency = inv.currency

        payment = Payment(
            id=uuid.uuid4(),
            organization_id=organization_id,
            customer_id=customer_id,
            invoice_id=invoice_id,
            payment_reference=PaymentService.generate_payment_reference(),
            amount=amount.quantize(Decimal("0.01")),
            currency=currency,
            payment_method=payment_method.upper(),
            payment_date=datetime.now(timezone.utc),
            transaction_reference=transaction_reference,
            notes=notes,
            status=status.upper(),
            created_at=datetime.now(timezone.utc),
        )
        db.add(payment)
        db.flush()

        # If linked directly to an invoice and completed, allocate
        if invoice_id and payment.status == "COMPLETED":
            PaymentService.allocate_payment(
                db=db,
                organization_id=organization_id,
                payment_id=payment.id,
                invoice_id=invoice_id,
                amount=amount,
                notes="Automatic allocation upon payment recording",
            )

        db.commit()
        db.refresh(payment)
        return payment

    @staticmethod
    def allocate_payment(
        db: Session,
        organization_id: uuid.UUID,
        payment_id: uuid.UUID,
        invoice_id: uuid.UUID,
        amount: Decimal,
        notes: Optional[str] = None,
    ) -> PaymentAllocation:
        """
        Allocate an amount from a payment to an open invoice.
        Enforces:
        - Allocation cannot exceed remaining payment unallocated balance.
        - Allocation cannot exceed invoice remaining balance due.
        - Invoice status transitions to PARTIALLY_PAID or PAID based on exact balance.
        """
        payment = (
            db.query(Payment)
            .filter(Payment.id == payment_id, Payment.organization_id == organization_id)
            .first()
        )
        if not payment:
            raise EntityNotFoundException("Payment", str(payment_id))

        if payment.status != "COMPLETED":
            raise BusinessRuleValidationException(
                f"Cannot allocate payment in status '{payment.status}'. Only COMPLETED payments can be allocated."
            )

        invoice = (
            db.query(Invoice)
            .filter(Invoice.id == invoice_id, Invoice.organization_id == organization_id)
            .first()
        )
        if not invoice:
            raise EntityNotFoundException("Invoice", str(invoice_id))

        if invoice.status in ["CANCELLED", "VOIDED"]:
            raise BusinessRuleValidationException(
                f"Cannot allocate payment to an invoice with status '{invoice.status}'."
            )

        # Check existing allocations for this payment
        total_allocated_so_far = (
            db.query(func.coalesce(func.sum(PaymentAllocation.amount_allocated), Decimal("0.00")))
            .filter(PaymentAllocation.payment_id == payment.id)
            .scalar()
        )
        available_payment_balance = payment.amount - total_allocated_so_far
        if amount > available_payment_balance:
            raise BusinessRuleValidationException(
                f"Allocation amount ({amount}) exceeds available payment balance ({available_payment_balance})."
            )

        # Allocation cannot exceed invoice amount_due
        alloc_amount = min(amount, invoice.amount_due).quantize(Decimal("0.01"))
        if alloc_amount <= Decimal("0.00"):
            raise BusinessRuleValidationException(
                f"Invoice {invoice.invoice_number} is already fully paid (amount due: 0.00)."
            )

        allocation = PaymentAllocation(
            id=uuid.uuid4(),
            payment_id=payment.id,
            invoice_id=invoice.id,
            amount_allocated=alloc_amount,
            allocated_at=datetime.now(timezone.utc),
            notes=notes,
        )
        db.add(allocation)

        # Update invoice balances
        invoice.amount_paid = (invoice.amount_paid + alloc_amount).quantize(Decimal("0.01"))
        invoice.amount_due = max(Decimal("0.00"), invoice.total_amount - invoice.amount_paid).quantize(
            Decimal("0.01")
        )

        # Update invoice status deterministically
        if invoice.amount_due == Decimal("0.00"):
            invoice.status = "PAID"
        else:
            invoice.status = "PARTIALLY_PAID"

        invoice.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(allocation)
        return allocation

    @staticmethod
    def refund_payment(
        db: Session,
        organization_id: uuid.UUID,
        payment_id: uuid.UUID,
        amount: Decimal,
        reason: str,
    ) -> PaymentRefund:
        """
        Record refund against a payment.
        Validates refund amount does not exceed payment amount.
        """
        payment = (
            db.query(Payment)
            .filter(Payment.id == payment_id, Payment.organization_id == organization_id)
            .first()
        )
        if not payment:
            raise EntityNotFoundException("Payment", str(payment_id))

        if amount <= Decimal("0.00"):
            raise BusinessRuleValidationException("Refund amount must be greater than zero.")

        # Check total previous refunds
        prior_refunds = (
            db.query(func.coalesce(func.sum(PaymentRefund.amount), Decimal("0.00")))
            .filter(PaymentRefund.payment_id == payment.id, PaymentRefund.status == "COMPLETED")
            .scalar()
        )
        if amount > (payment.amount - prior_refunds):
            raise BusinessRuleValidationException(
                f"Refund amount {amount} exceeds remaining refundable balance {payment.amount - prior_refunds}."
            )

        refund_ref = f"REF-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        refund = PaymentRefund(
            id=uuid.uuid4(),
            payment_id=payment.id,
            refund_reference=refund_ref,
            amount=amount.quantize(Decimal("0.01")),
            reason=reason,
            refund_date=datetime.now(timezone.utc),
            status="COMPLETED",
            created_at=datetime.now(timezone.utc),
        )
        db.add(refund)

        # Update payment status
        new_total_refunded = prior_refunds + amount
        if new_total_refunded >= payment.amount:
            payment.status = "REFUNDED"
        else:
            payment.status = "PARTIALLY_REFUNDED"

        db.commit()
        db.refresh(refund)
        return refund

    @staticmethod
    def get_payments(
        db: Session,
        organization_id: uuid.UUID,
        customer_id: Optional[uuid.UUID] = None,
        page: int = 1,
        per_page: int = 50,
    ) -> Tuple[List[Payment], int]:
        query = db.query(Payment).filter(Payment.organization_id == organization_id)
        if customer_id:
            query = query.filter(Payment.customer_id == customer_id)
        total = query.count()
        payments = (
            query.order_by(Payment.payment_date.desc(), Payment.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        return payments, total

    @staticmethod
    def get_payment_by_id(
        db: Session, organization_id: uuid.UUID, payment_id: uuid.UUID
    ) -> Optional[Payment]:
        return (
            db.query(Payment)
            .filter(Payment.id == payment_id, Payment.organization_id == organization_id)
            .first()
        )

    @staticmethod
    def get_invoice_payments(
        db: Session, organization_id: uuid.UUID, invoice_id: uuid.UUID
    ) -> List[PaymentAllocation]:
        return (
            db.query(PaymentAllocation)
            .join(Payment)
            .filter(
                PaymentAllocation.invoice_id == invoice_id,
                Payment.organization_id == organization_id,
            )
            .all()
        )
