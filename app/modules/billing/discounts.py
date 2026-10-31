import uuid
from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.modules.billing.models import Discount, DiscountRedemption, Invoice


class DiscountService:
    @staticmethod
    def create_discount(
        db: Session,
        organization_id: uuid.UUID,
        discount_name: str,
        discount_type: str,
        discount_value: Decimal,
        discount_code: Optional[str] = None,
        minimum_purchase: Decimal = Decimal("0.00"),
        minimum_quantity: int = 0,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        usage_limit: Optional[int] = None,
        product_id: Optional[uuid.UUID] = None,
        subscription_wide: bool = True,
        active: bool = True,
    ) -> Discount:
        disc = Discount(
            id=uuid.uuid4(),
            organization_id=organization_id,
            discount_name=discount_name,
            discount_code=discount_code.upper() if discount_code else None,
            discount_type=discount_type.upper(),  # FIXED, PERCENTAGE
            discount_value=discount_value.quantize(Decimal("0.01")),
            minimum_purchase=minimum_purchase.quantize(Decimal("0.01")),
            minimum_quantity=minimum_quantity,
            start_date=start_date or date.today(),
            end_date=end_date,
            usage_limit=usage_limit,
            usage_count=0,
            product_id=product_id,
            subscription_wide=subscription_wide,
            active=active,
        )
        db.add(disc)
        db.commit()
        db.refresh(disc)
        return disc

    @staticmethod
    def get_discounts(
        db: Session,
        organization_id: uuid.UUID,
        active_only: bool = False,
    ) -> List[Discount]:
        query = db.query(Discount).filter(Discount.organization_id == organization_id)
        if active_only:
            today = date.today()
            query = query.filter(
                Discount.active == True,
                Discount.start_date <= today,
                (Discount.end_date == None) | (Discount.end_date >= today),
            )
        return query.all()

    @staticmethod
    def get_discount_by_id(
        db: Session, organization_id: uuid.UUID, discount_id: uuid.UUID
    ) -> Optional[Discount]:
        return (
            db.query(Discount)
            .filter(Discount.id == discount_id, Discount.organization_id == organization_id)
            .first()
        )

    @staticmethod
    def update_discount(
        db: Session, organization_id: uuid.UUID, discount_id: uuid.UUID, **kwargs
    ) -> Optional[Discount]:
        disc = DiscountService.get_discount_by_id(db, organization_id, discount_id)
        if not disc:
            return None
        for key, value in kwargs.items():
            if value is not None and hasattr(disc, key):
                if key == "discount_value" and isinstance(value, (int, float, str, Decimal)):
                    value = Decimal(str(value)).quantize(Decimal("0.01"))
                elif key == "minimum_purchase" and isinstance(value, (int, float, str, Decimal)):
                    value = Decimal(str(value)).quantize(Decimal("0.01"))
                elif key == "discount_type":
                    value = str(value).upper()
                setattr(disc, key, value)
        db.commit()
        db.refresh(disc)
        return disc

    @staticmethod
    def validate_discount(
        discount: Discount,
        purchase_subtotal: Decimal,
        quantity: int = 1,
        evaluation_date: Optional[date] = None,
    ) -> Tuple[bool, str]:
        """Validate eligibility against date, minimum purchase, minimum quantity, usage limits."""
        eval_date = evaluation_date or date.today()

        if not discount.active:
            return False, "Discount is inactive."

        if discount.start_date and eval_date < discount.start_date:
            return False, f"Discount is not effective until {discount.start_date}."

        if discount.end_date and eval_date > discount.end_date:
            return False, f"Discount expired on {discount.end_date}."

        if discount.usage_limit is not None and discount.usage_count >= discount.usage_limit:
            return False, f"Discount usage limit of {discount.usage_limit} redemptions reached."

        if purchase_subtotal < discount.minimum_purchase:
            return (
                False,
                f"Minimum purchase amount of {discount.minimum_purchase} required (current: {purchase_subtotal}).",
            )

        if quantity < discount.minimum_quantity:
            return (
                False,
                f"Minimum quantity of {discount.minimum_quantity} required (current: {quantity}).",
            )

        return True, "Eligible"

    @staticmethod
    def calculate_discount_amount(
        discount: Discount,
        applicable_subtotal: Decimal,
    ) -> Decimal:
        """Calculate discount amount in currency with deterministic precision."""
        if applicable_subtotal <= Decimal("0.00"):
            return Decimal("0.00")

        if discount.discount_type == "PERCENTAGE":
            rate = discount.discount_value
            if rate > Decimal("1.00"):
                rate = rate / Decimal("100.00")
            amt = (applicable_subtotal * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            return min(amt, applicable_subtotal)
        else:  # FIXED
            return min(discount.discount_value, applicable_subtotal).quantize(Decimal("0.01"))

    @staticmethod
    def redeem_discount(
        db: Session,
        discount_id: uuid.UUID,
        invoice_id: uuid.UUID,
        customer_id: uuid.UUID,
        amount_applied: Decimal,
    ) -> Optional[DiscountRedemption]:
        """
        Record redemption and increment usage_count with concurrency safety.
        """
        # Lock discount row for update if supported, or verify usage limit atomically
        disc = db.query(Discount).filter(Discount.id == discount_id).with_for_update().first()
        if not disc or not disc.active:
            return None

        if disc.usage_limit is not None and disc.usage_count >= disc.usage_limit:
            return None

        disc.usage_count += 1
        redemption = DiscountRedemption(
            id=uuid.uuid4(),
            discount_id=disc.id,
            invoice_id=invoice_id,
            customer_id=customer_id,
            amount_applied=amount_applied.quantize(Decimal("0.01")),
            redeemed_at=datetime.now(timezone.utc),
        )
        db.add(redemption)
        db.flush()
        return redemption
