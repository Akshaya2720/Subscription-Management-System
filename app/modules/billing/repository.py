"""Repository layer for Taxes, Discounts, Invoices, and Payments."""

import uuid
from decimal import Decimal
from datetime import date, datetime
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import or_

from app.models.billing import (
    TaxRule,
    Discount,
    Invoice,
    InvoiceItem,
    InvoiceStatusHistory,
    Payment,
    InvoiceStatus,
    DiscountType,
)


class TaxRuleRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, org_id: uuid.UUID, tax_id: uuid.UUID) -> Optional[TaxRule]:
        return self.db.query(TaxRule).filter(TaxRule.organization_id == org_id, TaxRule.id == tax_id).first()

    def get_by_code(self, org_id: uuid.UUID, tax_code: str) -> Optional[TaxRule]:
        return self.db.query(TaxRule).filter(TaxRule.organization_id == org_id, TaxRule.tax_code == tax_code).first()

    def get_default_or_matching(
        self, org_id: uuid.UUID, country: Optional[str] = None, state_province: Optional[str] = None
    ) -> Optional[TaxRule]:
        """Match by country/state or fall back to default tax rule."""
        if country and state_province:
            match = (
                self.db.query(TaxRule)
                .filter(
                    TaxRule.organization_id == org_id,
                    TaxRule.country.ilike(country),
                    TaxRule.state_province.ilike(state_province),
                    TaxRule.is_active == True,
                )
                .first()
            )
            if match:
                return match

        if country:
            match = (
                self.db.query(TaxRule)
                .filter(
                    TaxRule.organization_id == org_id,
                    TaxRule.country.ilike(country),
                    TaxRule.is_active == True,
                )
                .first()
            )
            if match:
                return match

        return (
            self.db.query(TaxRule)
            .filter(TaxRule.organization_id == org_id, TaxRule.is_default == True, TaxRule.is_active == True)
            .first()
        )

    def list(self, org_id: uuid.UUID) -> List[TaxRule]:
        return (
            self.db.query(TaxRule)
            .filter(TaxRule.organization_id == org_id)
            .order_by(TaxRule.created_at.desc())
            .all()
        )

    def save(self, rule: TaxRule) -> TaxRule:
        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)
        return rule


class DiscountRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, org_id: uuid.UUID, discount_id: uuid.UUID) -> Optional[Discount]:
        return self.db.query(Discount).filter(Discount.organization_id == org_id, Discount.id == discount_id).first()

    def get_by_code(self, org_id: uuid.UUID, code: str) -> Optional[Discount]:
        return self.db.query(Discount).filter(Discount.organization_id == org_id, Discount.code == code.upper()).first()

    def list(self, org_id: uuid.UUID) -> List[Discount]:
        return (
            self.db.query(Discount)
            .filter(Discount.organization_id == org_id)
            .order_by(Discount.created_at.desc())
            .all()
        )

    def increment_usage(self, discount: Discount) -> None:
        discount.times_used += 1
        self.db.flush()

    def save(self, discount: Discount) -> Discount:
        self.db.add(discount)
        self.db.commit()
        self.db.refresh(discount)
        return discount


class InvoiceRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, org_id: uuid.UUID, invoice_id: uuid.UUID) -> Optional[Invoice]:
        return (
            self.db.query(Invoice)
            .options(selectinload(Invoice.items))
            .filter(Invoice.organization_id == org_id, Invoice.id == invoice_id)
            .first()
        )

    def get_by_subscription_and_period(
        self, subscription_id: uuid.UUID, period_start: date, period_end: date
    ) -> Optional[Invoice]:
        return (
            self.db.query(Invoice)
            .filter(
                Invoice.subscription_id == subscription_id,
                Invoice.period_start == period_start,
                Invoice.period_end == period_end,
            )
            .first()
        )

    def list(
        self,
        org_id: uuid.UUID,
        customer_id: Optional[uuid.UUID] = None,
        status: Optional[InvoiceStatus] = None,
        due_date_before: Optional[date] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> Tuple[List[Invoice], int]:
        query = self.db.query(Invoice).filter(Invoice.organization_id == org_id)
        if customer_id:
            query = query.filter(Invoice.customer_id == customer_id)
        if status:
            query = query.filter(Invoice.status == status)
        if due_date_before:
            query = query.filter(Invoice.due_date <= due_date_before)

        total = query.count()
        items = (
            query.options(selectinload(Invoice.items))
            .order_by(Invoice.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        return items, total

    def save(self, invoice: Invoice) -> Invoice:
        self.db.add(invoice)
        self.db.commit()
        self.db.refresh(invoice)
        return invoice

    def log_status_change(self, invoice_id: uuid.UUID, from_status: str, to_status: str, reason: str = "") -> None:
        history = InvoiceStatusHistory(
            invoice_id=invoice_id,
            from_status=from_status,
            to_status=to_status,
            reason=reason,
        )
        self.db.add(history)
        self.db.flush()


class PaymentRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, payment_id: uuid.UUID) -> Optional[Payment]:
        return self.db.get(Payment, payment_id)

    def list_by_invoice(self, invoice_id: uuid.UUID) -> List[Payment]:
        return self.db.query(Payment).filter(Payment.invoice_id == invoice_id).order_by(Payment.created_at.desc()).all()

    def save(self, payment: Payment) -> Payment:
        self.db.add(payment)
        self.db.commit()
        self.db.refresh(payment)
        return payment
