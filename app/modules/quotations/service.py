import uuid
import random
from decimal import Decimal
from datetime import datetime, date, timezone
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.modules.quotations.models import Quotation, QuotationItem
from app.modules.quotations.schemas import (
    QuotationCreate,
    QuotationUpdate,
    ConvertToSubscriptionRequest,
)
from app.modules.customers.service import CustomerService
from app.modules.products.models import Product, ProductVariant
from app.modules.plans.models import SubscriptionPlan
from app.modules.billing.interfaces import DefaultTaxDiscountService, BillingItemInput
from app.core.exceptions import (
    EntityNotFoundException,
    DuplicateEntityException,
    InvalidStateTransitionException,
    BusinessRuleValidationException,
)


class QuotationService:
    @staticmethod
    def _generate_quotation_number() -> str:
        today_str = datetime.now().strftime("%Y%m%d")
        rand_num = random.randint(1000, 9999)
        return f"QTN-{today_str}-{rand_num}"

    @staticmethod
    def create_quotation(db: Session, org_id: uuid.UUID, data: QuotationCreate) -> Quotation:
        # Validate customer
        CustomerService.get_customer(db, org_id, data.customer_id)

        quotation_num = data.quotation_number or QuotationService._generate_quotation_number()
        # Verify unique quotation_number
        existing = (
            db.query(Quotation)
            .filter(Quotation.organization_id == org_id, Quotation.quotation_number == quotation_num)
            .first()
        )
        if existing:
            quotation_num = QuotationService._generate_quotation_number()

        quotation = Quotation(
            organization_id=org_id,
            customer_id=data.customer_id,
            quotation_number=quotation_num,
            quotation_date=data.quotation_date or date.today(),
            expiry_date=data.expiry_date,
            status="DRAFT",
            notes=data.notes,
            subtotal=Decimal("0.00"),
            discount_total=data.discount_total or Decimal("0.00"),
            tax_total=Decimal("0.00"),
            grand_total=Decimal("0.00"),
        )
        db.add(quotation)
        db.flush()

        # Build items with snapshots
        billing_inputs: List[BillingItemInput] = []
        for item_data in data.items:
            product = (
                db.query(Product)
                .filter(Product.organization_id == org_id, Product.id == item_data.product_id)
                .first()
            )
            if not product:
                raise EntityNotFoundException("Product", str(item_data.product_id))

            variant = None
            if item_data.variant_id:
                variant = (
                    db.query(ProductVariant)
                    .filter(
                        ProductVariant.product_id == product.id,
                        ProductVariant.id == item_data.variant_id,
                    )
                    .first()
                )
                if not variant:
                    raise EntityNotFoundException("ProductVariant", str(item_data.variant_id))

            # Calculate snapshot unit price
            if item_data.unit_price is not None:
                unit_price = item_data.unit_price
            else:
                base_price = product.sales_price
                variant_price = variant.additional_price if variant else Decimal("0.00")
                unit_price = base_price + variant_price

            description = item_data.description
            if not description:
                description = product.name
                if variant:
                    description += f" ({variant.variant_name})"

            line_total = (unit_price * item_data.quantity).quantize(Decimal("0.01"))

            q_item = QuotationItem(
                quotation_id=quotation.id,
                product_id=product.id,
                variant_id=variant.id if variant else None,
                plan_id=item_data.plan_id,
                description=description,
                quantity=item_data.quantity,
                unit_price=unit_price,
                tax_configuration_reference=item_data.tax_configuration_reference,
                line_total=line_total,
            )
            db.add(q_item)

            billing_inputs.append(
                BillingItemInput(
                    product_id=product.id,
                    variant_id=variant.id if variant else None,
                    description=description,
                    quantity=item_data.quantity,
                    unit_price=unit_price,
                    tax_reference=item_data.tax_configuration_reference,
                )
            )

        # Compute totals using Member 3 TaxDiscountInterface
        tax_service = DefaultTaxDiscountService()
        primary_tax_ref = (
            billing_inputs[0].tax_reference
            if billing_inputs and billing_inputs[0].tax_reference
            else None
        )
        tax_result = tax_service.calculate_totals(
            billing_inputs,
            discount_rate_or_amount=data.discount_total,
            tax_code=primary_tax_ref,
        )

        quotation.subtotal = tax_result.subtotal
        quotation.discount_total = tax_result.discount_total
        quotation.tax_total = tax_result.tax_total
        quotation.grand_total = tax_result.grand_total

        db.commit()
        db.refresh(quotation)
        return quotation

    @staticmethod
    def get_quotation(db: Session, org_id: uuid.UUID, quotation_id: uuid.UUID) -> Quotation:
        quotation = (
            db.query(Quotation)
            .filter(Quotation.organization_id == org_id, Quotation.id == quotation_id)
            .first()
        )
        if not quotation:
            raise EntityNotFoundException("Quotation", str(quotation_id))
        return quotation

    @staticmethod
    def update_quotation(db: Session, org_id: uuid.UUID, quotation_id: uuid.UUID, data: QuotationUpdate) -> Quotation:
        quotation = QuotationService.get_quotation(db, org_id, quotation_id)

        if quotation.status != "DRAFT":
            raise InvalidStateTransitionException(
                current_status=quotation.status,
                target_status="UPDATED",
                reason="Only DRAFT quotations can be modified.",
            )

        recalculate_totals = False
        if data.expiry_date is not None:
            quotation.expiry_date = data.expiry_date
        if data.notes is not None:
            quotation.notes = data.notes
        if data.discount_total is not None:
            quotation.discount_total = data.discount_total
            recalculate_totals = True

        if data.items is not None:
            recalculate_totals = True
            # Clear old items
            db.query(QuotationItem).filter(QuotationItem.quotation_id == quotation.id).delete()
            db.flush()

            for item_data in data.items:
                product = (
                    db.query(Product)
                    .filter(Product.organization_id == org_id, Product.id == item_data.product_id)
                    .first()
                )
                if not product:
                    raise EntityNotFoundException("Product", str(item_data.product_id))

                variant = None
                if item_data.variant_id:
                    variant = (
                        db.query(ProductVariant)
                        .filter(ProductVariant.product_id == product.id, ProductVariant.id == item_data.variant_id)
                        .first()
                    )

                unit_price = item_data.unit_price
                if unit_price is None:
                    unit_price = product.sales_price + (variant.additional_price if variant else Decimal("0.00"))

                desc = item_data.description or product.name + (f" ({variant.variant_name})" if variant else "")
                line_total = (unit_price * item_data.quantity).quantize(Decimal("0.01"))

                q_item = QuotationItem(
                    quotation_id=quotation.id,
                    product_id=product.id,
                    variant_id=variant.id if variant else None,
                    plan_id=item_data.plan_id,
                    description=desc,
                    quantity=item_data.quantity,
                    unit_price=unit_price,
                    tax_configuration_reference=item_data.tax_configuration_reference,
                    line_total=line_total,
                )
                db.add(q_item)

        if recalculate_totals:
            db.flush()
            # Fetch all current items
            current_items = db.query(QuotationItem).filter(QuotationItem.quotation_id == quotation.id).all()
            billing_inputs: List[BillingItemInput] = [
                BillingItemInput(
                    product_id=it.product_id,
                    variant_id=it.variant_id,
                    description=it.description,
                    quantity=it.quantity,
                    unit_price=it.unit_price,
                    tax_reference=it.tax_configuration_reference,
                )
                for it in current_items
            ]
            tax_service = DefaultTaxDiscountService()
            primary_tax_ref = billing_inputs[0].tax_reference if billing_inputs else None
            tax_result = tax_service.calculate_totals(
                billing_inputs,
                discount_rate_or_amount=quotation.discount_total,
                tax_code=primary_tax_ref,
            )
            quotation.subtotal = tax_result.subtotal
            quotation.discount_total = tax_result.discount_total
            quotation.tax_total = tax_result.tax_total
            quotation.grand_total = tax_result.grand_total

        db.commit()
        db.refresh(quotation)
        return quotation

    @staticmethod
    def confirm_quotation(db: Session, org_id: uuid.UUID, quotation_id: uuid.UUID) -> Quotation:
        quotation = QuotationService.get_quotation(db, org_id, quotation_id)

        if quotation.status != "DRAFT":
            raise InvalidStateTransitionException(
                current_status=quotation.status,
                target_status="CONFIRMED",
                reason="Only DRAFT quotations can be confirmed.",
            )

        if quotation.expiry_date < date.today():
            quotation.status = "EXPIRED"
            db.commit()
            raise BusinessRuleValidationException(
                f"Quotation {quotation.quotation_number} has expired on {quotation.expiry_date}."
            )

        quotation.status = "CONFIRMED"
        db.commit()
        db.refresh(quotation)
        return quotation

    @staticmethod
    def cancel_quotation(db: Session, org_id: uuid.UUID, quotation_id: uuid.UUID) -> Quotation:
        quotation = QuotationService.get_quotation(db, org_id, quotation_id)

        if quotation.status in ("CONVERTED", "CANCELLED"):
            raise InvalidStateTransitionException(
                current_status=quotation.status,
                target_status="CANCELLED",
                reason=f"Cannot cancel a quotation in '{quotation.status}' status.",
            )

        quotation.status = "CANCELLED"
        db.commit()
        db.refresh(quotation)
        return quotation

    @staticmethod
    def list_quotations(
        db: Session,
        org_id: uuid.UUID,
        customer_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> Tuple[List[Quotation], int]:
        query = db.query(Quotation).filter(Quotation.organization_id == org_id)

        if customer_id:
            query = query.filter(Quotation.customer_id == customer_id)

        if status:
            query = query.filter(Quotation.status == status.upper())

        total = query.count()
        items = query.order_by(Quotation.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
        return items, total

    @staticmethod
    def convert_to_subscription(
        db: Session, org_id: uuid.UUID, quotation_id: uuid.UUID, payload: ConvertToSubscriptionRequest
    ):
        """Converts a confirmed quotation into an active/confirmed subscription."""
        quotation = QuotationService.get_quotation(db, org_id, quotation_id)

        if quotation.status != "CONFIRMED":
            raise InvalidStateTransitionException(
                current_status=quotation.status,
                target_status="CONVERTED",
                reason="Only CONFIRMED quotations can be converted into subscriptions.",
            )

        if quotation.expiry_date < date.today():
            quotation.status = "EXPIRED"
            db.commit()
            raise BusinessRuleValidationException(
                f"Quotation {quotation.quotation_number} has expired and cannot be converted."
            )

        from app.modules.subscriptions.service import SubscriptionService
        subscription = SubscriptionService.create_from_quotation(
            db=db, org_id=org_id, quotation=quotation, payload=payload
        )

        quotation.status = "CONVERTED"
        db.commit()
        db.refresh(quotation)
        return subscription
