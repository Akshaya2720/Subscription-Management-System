import uuid
from datetime import date, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_

from app.modules.billing.models import TaxRule


class TaxService:
    @staticmethod
    def create_tax_rule(
        db: Session,
        organization_id: uuid.UUID,
        name: str,
        tax_rate: Decimal,
        tax_type: str = "GST",
        inclusive_or_exclusive: str = "EXCLUSIVE",
        effective_from: Optional[date] = None,
        effective_until: Optional[date] = None,
        active: bool = True,
    ) -> TaxRule:
        rule = TaxRule(
            id=uuid.uuid4(),
            organization_id=organization_id,
            name=name,
            tax_rate=tax_rate.quantize(Decimal("0.0001")),
            tax_type=tax_type.upper(),
            inclusive_or_exclusive=inclusive_or_exclusive.upper(),
            effective_from=effective_from or date.today(),
            effective_until=effective_until,
            active=active,
        )
        db.add(rule)
        db.commit()
        db.refresh(rule)
        return rule

    @staticmethod
    def get_tax_rules(
        db: Session,
        organization_id: uuid.UUID,
        active_only: bool = True,
    ) -> List[TaxRule]:
        query = db.query(TaxRule).filter(TaxRule.organization_id == organization_id)
        if active_only:
            today = date.today()
            query = query.filter(
                TaxRule.active == True,
                TaxRule.effective_from <= today,
                or_(TaxRule.effective_until == None, TaxRule.effective_until >= today),
            )
        return query.all()

    @staticmethod
    def update_tax_rule(
        db: Session,
        organization_id: uuid.UUID,
        rule_id: uuid.UUID,
        **kwargs,
    ) -> Optional[TaxRule]:
        rule = (
            db.query(TaxRule)
            .filter(TaxRule.id == rule_id, TaxRule.organization_id == organization_id)
            .first()
        )
        if not rule:
            return None
        for key, value in kwargs.items():
            if value is not None and hasattr(rule, key):
                if key == "tax_rate" and isinstance(value, (int, float, str, Decimal)):
                    value = Decimal(str(value)).quantize(Decimal("0.0001"))
                setattr(rule, key, value)
        db.commit()
        db.refresh(rule)
        return rule

    @staticmethod
    def calculate_taxes(
        subtotal_after_discounts: Decimal,
        tax_rules: List[TaxRule],
    ) -> Tuple[Decimal, Decimal, Dict[str, Decimal]]:
        """
        Calculate total tax, effective base amount, and itemized breakdown.
        Deterministic Decimal arithmetic with ROUND_HALF_UP to 2 decimal places.
        
        Returns:
            (taxable_base, total_tax, breakdown_dict)
        """
        if subtotal_after_discounts <= Decimal("0.00") or not tax_rules:
            return (
                max(Decimal("0.00"), subtotal_after_discounts).quantize(Decimal("0.01")),
                Decimal("0.00"),
                {},
            )

        # Check if any rule is tax-inclusive
        inclusive_rules = [r for r in tax_rules if r.inclusive_or_exclusive == "INCLUSIVE"]
        exclusive_rules = [r for r in tax_rules if r.inclusive_or_exclusive == "EXCLUSIVE"]

        total_tax = Decimal("0.00")
        breakdown: Dict[str, Decimal] = {}

        if inclusive_rules:
            # Inclusive: Subtotal already contains tax.
            # Base = Subtotal / (1 + sum(inclusive_rates))
            combined_inclusive_rate = sum(r.tax_rate for r in inclusive_rules)
            taxable_base = (
                subtotal_after_discounts / (Decimal("1.0000") + combined_inclusive_rate)
            ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            for rule in inclusive_rules:
                rule_tax = (taxable_base * rule.tax_rate).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )
                total_tax += rule_tax
                breakdown[rule.name] = rule_tax
        else:
            taxable_base = subtotal_after_discounts.quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )

        # Exclusive rules apply on top of taxable_base
        for rule in exclusive_rules:
            rule_tax = (taxable_base * rule.tax_rate).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            total_tax += rule_tax
            breakdown[rule.name] = rule_tax

        return taxable_base, total_tax.quantize(Decimal("0.01")), breakdown
