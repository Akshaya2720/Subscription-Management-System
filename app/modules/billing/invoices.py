import io
import os
import uuid
from datetime import date, datetime, timezone, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_, func

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from app.core.exceptions import (
    EntityNotFoundException,
    InvalidStateTransitionException,
    BusinessRuleValidationException,
)
from app.modules.billing.models import Invoice, InvoiceItem, TaxRule, Discount
from app.modules.customers.models import Customer
from app.modules.billing.taxes import TaxService
from app.modules.billing.discounts import DiscountService


class InvoiceService:
    @staticmethod
    def generate_invoice_number(db: Session, organization_id: uuid.UUID) -> str:
        """Generate deterministic sequential invoice number: INV-YYYY-XXXXX."""
        year = date.today().year
        prefix = f"INV-{year}-"
        count = (
            db.query(func.count(Invoice.id))
            .filter(
                Invoice.organization_id == organization_id,
                Invoice.invoice_number.like(f"{prefix}%"),
            )
            .scalar()
            or 0
        )
        return f"{prefix}{count + 1:04d}"

    @staticmethod
    def create_invoice(
        db: Session,
        organization_id: uuid.UUID,
        customer_id: uuid.UUID,
        subscription_id: Optional[uuid.UUID],
        due_date: date,
        items_data: List[Dict[str, Any]],
        billing_period_start: Optional[date] = None,
        billing_period_end: Optional[date] = None,
        currency: str = "INR",
        invoice_type: str = "RECURRING",
        discount_id: Optional[uuid.UUID] = None,
        tax_rule_ids: Optional[List[uuid.UUID]] = None,
        notes: Optional[str] = None,
        status: str = "DRAFT",
    ) -> Invoice:
        customer = (
            db.query(Customer)
            .filter(Customer.id == customer_id, Customer.organization_id == organization_id)
            .first()
        )
        if not customer:
            raise EntityNotFoundException("Customer", str(customer_id))

        invoice_number = InvoiceService.generate_invoice_number(db, organization_id)
        issue_date = date.today()

        # Build items and calculate subtotal
        subtotal = Decimal("0.00")
        built_items = []
        for it in items_data:
            qty = int(it.get("quantity", 1))
            unit_price = Decimal(str(it["unit_price"])).quantize(Decimal("0.01"))
            line_subtotal = (unit_price * qty).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            subtotal += line_subtotal
            
            built_items.append({
                "product_id": it.get("product_id"),
                "variant_id": it.get("variant_id"),
                "description_snapshot": it["description_snapshot"],
                "quantity": qty,
                "unit_price": unit_price,
                "discount_amount": Decimal("0.00"),
                "tax_amount": Decimal("0.00"),
                "line_total": line_subtotal,
            })

        # Calculate discount
        discount_total = Decimal("0.00")
        applied_discount: Optional[Discount] = None
        if discount_id:
            applied_discount = DiscountService.get_discount_by_id(db, organization_id, discount_id)
            if applied_discount:
                valid, msg = DiscountService.validate_discount(
                    applied_discount, purchase_subtotal=subtotal, quantity=sum(i["quantity"] for i in built_items)
                )
                if valid:
                    discount_total = DiscountService.calculate_discount_amount(applied_discount, subtotal)

        subtotal_after_discount = max(Decimal("0.00"), subtotal - discount_total)

        # Calculate taxes
        active_rules = []
        if tax_rule_ids:
            active_rules = (
                db.query(TaxRule)
                .filter(
                    TaxRule.id.in_(tax_rule_ids),
                    TaxRule.organization_id == organization_id,
                    TaxRule.active == True,
                )
                .all()
            )
        else:
            # Use active organization tax rules
            active_rules = TaxService.get_tax_rules(db, organization_id, active_only=True)

        taxable_base, tax_total, breakdown = TaxService.calculate_taxes(
            subtotal_after_discount, active_rules
        )
        grand_total = (taxable_base + tax_total).quantize(Decimal("0.01"))

        # Distribute taxes and discounts across items proportionally
        if subtotal > Decimal("0.00"):
            for i in built_items:
                ratio = (i["line_total"] / subtotal).quantize(Decimal("0.0001"))
                i_discount = (discount_total * ratio).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                i_tax = (tax_total * ratio).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                i["discount_amount"] = i_discount
                i["tax_amount"] = i_tax
                i["line_total"] = (i["line_total"] - i_discount + i_tax).quantize(Decimal("0.01"))

        invoice = Invoice(
            id=uuid.uuid4(),
            organization_id=organization_id,
            customer_id=customer_id,
            subscription_id=subscription_id,
            invoice_number=invoice_number,
            issue_date=issue_date,
            due_date=due_date,
            billing_period_start=billing_period_start,
            billing_period_end=billing_period_end,
            currency=currency,
            subtotal=subtotal,
            discount_total=discount_total,
            tax_total=tax_total,
            total_amount=grand_total,
            amount_paid=Decimal("0.00"),
            amount_due=grand_total,
            status=status.upper(),
            invoice_type=invoice_type.upper(),
            verification_status="PENDING",
            notes=notes,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(invoice)
        db.flush()

        for bi in built_items:
            item_record = InvoiceItem(
                id=uuid.uuid4(),
                invoice_id=invoice.id,
                product_id=bi["product_id"],
                variant_id=bi["variant_id"],
                description_snapshot=bi["description_snapshot"],
                quantity=bi["quantity"],
                unit_price=bi["unit_price"],
                discount_amount=bi["discount_amount"],
                tax_amount=bi["tax_amount"],
                line_total=bi["line_total"],
                created_at=datetime.now(timezone.utc),
            )
            db.add(item_record)

        if applied_discount and discount_total > Decimal("0.00"):
            DiscountService.redeem_discount(
                db,
                discount_id=applied_discount.id,
                invoice_id=invoice.id,
                customer_id=customer_id,
                amount_applied=discount_total,
            )

        db.commit()
        db.refresh(invoice)
        return invoice

    @staticmethod
    def get_invoices(
        db: Session,
        organization_id: uuid.UUID,
        search: Optional[str] = None,
        status: Optional[str] = None,
        customer_id: Optional[uuid.UUID] = None,
        subscription_id: Optional[uuid.UUID] = None,
        page: int = 1,
        per_page: int = 50,
    ) -> Tuple[List[Invoice], int]:
        query = db.query(Invoice).filter(Invoice.organization_id == organization_id)
        if customer_id:
            query = query.filter(Invoice.customer_id == customer_id)
        if subscription_id:
            query = query.filter(Invoice.subscription_id == subscription_id)
        if status and status.lower() != "all":
            query = query.filter(Invoice.status == status.upper())
        if search:
            s = f"%{search}%"
            query = query.join(Customer).filter(
                or_(
                    Invoice.invoice_number.ilike(s),
                    Customer.name.ilike(s),
                    Customer.email.ilike(s),
                )
            )

        total = query.count()
        invoices = (
            query.order_by(Invoice.issue_date.desc(), Invoice.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        return invoices, total

    @staticmethod
    def get_invoice_by_id(
        db: Session, organization_id: uuid.UUID, invoice_id: uuid.UUID
    ) -> Optional[Invoice]:
        return (
            db.query(Invoice)
            .filter(Invoice.id == invoice_id, Invoice.organization_id == organization_id)
            .first()
        )

    @staticmethod
    def confirm_invoice(
        db: Session, organization_id: uuid.UUID, invoice_id: uuid.UUID
    ) -> Invoice:
        invoice = InvoiceService.get_invoice_by_id(db, organization_id, invoice_id)
        if not invoice:
            raise EntityNotFoundException("Invoice", str(invoice_id))
        if invoice.status not in ["DRAFT"]:
            raise InvalidStateTransitionException(
                current_status=invoice.status,
                target_status="CONFIRMED",
                reason="Only DRAFT invoices can be confirmed.",
            )
        invoice.status = "CONFIRMED"
        invoice.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(invoice)
        return invoice

    @staticmethod
    def cancel_invoice(
        db: Session, organization_id: uuid.UUID, invoice_id: uuid.UUID, reason: Optional[str] = None
    ) -> Invoice:
        invoice = InvoiceService.get_invoice_by_id(db, organization_id, invoice_id)
        if not invoice:
            raise EntityNotFoundException("Invoice", str(invoice_id))
        if invoice.status in ["PAID"]:
            raise InvalidStateTransitionException(
                current_status=invoice.status,
                target_status="CANCELLED",
                reason="Paid invoices cannot be cancelled directly. Issue a refund or credit note instead.",
            )
        if invoice.amount_paid > Decimal("0.00"):
            raise BusinessRuleValidationException(
                f"Invoice has active payments ({invoice.amount_paid}). Cannot cancel without refunding."
            )
        invoice.status = "CANCELLED"
        if reason:
            invoice.notes = f"{invoice.notes or ''}\nCancelled Reason: {reason}".strip()
        invoice.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(invoice)
        return invoice

    @staticmethod
    def update_invoice_status(
        db: Session, organization_id: uuid.UUID, invoice_id: uuid.UUID, new_status: str
    ) -> Invoice:
        invoice = InvoiceService.get_invoice_by_id(db, organization_id, invoice_id)
        if not invoice:
            raise EntityNotFoundException("Invoice", str(invoice_id))
        status_norm = new_status.upper()
        if status_norm == "PAID":
            # Guard: Only mark as paid if amount_paid covers total_amount
            if invoice.amount_paid < invoice.total_amount:
                # If marking paid manually, set amount_paid = total_amount and amount_due = 0
                invoice.amount_paid = invoice.total_amount
                invoice.amount_due = Decimal("0.00")
        invoice.status = status_norm
        invoice.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(invoice)
        return invoice

    @staticmethod
    def generate_pdf(invoice: Invoice) -> bytes:
        """Generate print-ready PDF invoice with itemized table snapshot."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36,
        )
        elements = []
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "InvoiceTitle",
            parent=styles["Heading1"],
            fontSize=22,
            leading=26,
            textColor=colors.HexColor("#1e293b"),
        )
        normal_style = styles["Normal"]
        bold_style = ParagraphStyle("Bold", parent=normal_style, fontName="Helvetica-Bold")

        # Header
        elements.append(Paragraph(f"<b>VERISUB INVOICE</b>", title_style))
        elements.append(Spacer(1, 12))

        # Meta info table
        cust_name = invoice.customer.name if invoice.customer else "Valued Customer"
        cust_email = invoice.customer.email if invoice.customer else "N/A"
        meta_data = [
            [
                Paragraph(f"<b>Invoice Number:</b> {invoice.invoice_number}", normal_style),
                Paragraph(f"<b>Billed To:</b> {cust_name}", normal_style),
            ],
            [
                Paragraph(f"<b>Issue Date:</b> {invoice.issue_date}", normal_style),
                Paragraph(f"<b>Email:</b> {cust_email}", normal_style),
            ],
            [
                Paragraph(f"<b>Due Date:</b> {invoice.due_date}", normal_style),
                Paragraph(f"<b>Currency:</b> {invoice.currency}", normal_style),
            ],
            [
                Paragraph(f"<b>Status:</b> {invoice.status}", normal_style),
                Paragraph(
                    f"<b>Billing Period:</b> {invoice.billing_period_start or 'N/A'} to {invoice.billing_period_end or 'N/A'}",
                    normal_style,
                ),
            ],
        ]
        meta_table = Table(meta_data, colWidths=[270, 270])
        meta_table.setStyle(
            TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ])
        )
        elements.append(meta_table)
        elements.append(Spacer(1, 16))

        # Line items table
        items_header = [
            Paragraph("<b>Description</b>", bold_style),
            Paragraph("<b>Qty</b>", bold_style),
            Paragraph("<b>Unit Price</b>", bold_style),
            Paragraph("<b>Discount</b>", bold_style),
            Paragraph("<b>Tax</b>", bold_style),
            Paragraph("<b>Total</b>", bold_style),
        ]
        item_rows = [items_header]
        for it in invoice.items:
            item_rows.append([
                Paragraph(it.description_snapshot, normal_style),
                str(it.quantity),
                f"{it.unit_price:.2f}",
                f"{it.discount_amount:.2f}",
                f"{it.tax_amount:.2f}",
                f"{it.line_total:.2f}",
            ])

        items_table = Table(item_rows, colWidths=[200, 40, 80, 70, 70, 80])
        items_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                ("ALIGN", (0, 0), (0, -1), "LEFT"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ])
        )
        elements.append(items_table)
        elements.append(Spacer(1, 16))

        # Totals summary table
        totals_data = [
            ["Subtotal:", f"{invoice.subtotal:.2f} {invoice.currency}"],
            ["Discount Total:", f"-{invoice.discount_total:.2f} {invoice.currency}"],
            ["Tax Total:", f"+{invoice.tax_total:.2f} {invoice.currency}"],
            ["Grand Total:", f"{invoice.total_amount:.2f} {invoice.currency}"],
            ["Amount Paid:", f"{invoice.amount_paid:.2f} {invoice.currency}"],
            ["Amount Due:", f"{invoice.amount_due:.2f} {invoice.currency}"],
        ]
        totals_table = Table(totals_data, colWidths=[400, 140])
        totals_table.setStyle(
            TableStyle([
                ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
                ("FONTNAME", (0, 3), (-1, 3), "Helvetica-Bold"),
                ("FONTNAME", (0, 5), (-1, 5), "Helvetica-Bold"),
                ("TEXTCOLOR", (0, 5), (-1, 5), colors.HexColor("#b91c1c") if invoice.amount_due > 0 else colors.HexColor("#15803d")),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ])
        )
        elements.append(totals_table)

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()
