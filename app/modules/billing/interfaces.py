"""
Member 3 Integration Interface Definition.
Defines the contract between Member 2 (Subscription Engine) and Member 3 (Billing & Verification).
"""
from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import uuid
from datetime import date


class BillingItemInput(BaseModel):
    product_id: uuid.UUID
    variant_id: Optional[uuid.UUID] = None
    description: str
    quantity: int
    unit_price: Decimal
    tax_reference: Optional[str] = None


class InvoiceGenerationInput(BaseModel):
    organization_id: uuid.UUID
    customer_id: uuid.UUID
    subscription_id: uuid.UUID
    billing_date: date
    due_date: date
    currency: str
    items: List[BillingItemInput]
    discount_total: Decimal = Decimal("0.00")
    tax_total: Decimal = Decimal("0.00")


class TaxCalculationResult(BaseModel):
    subtotal: Decimal
    discount_total: Decimal
    tax_total: Decimal
    grand_total: Decimal
    tax_breakdown: Dict[str, Decimal] = {}


class TaxDiscountServiceInterface(ABC):
    """
    Interface provided by Member 3 for calculating taxes and discounts.
    Member 2 delegates tax bracket computation to Member 3 and consumes the snapshot result.
    """

    @abstractmethod
    def calculate_totals(
        self,
        items: List[BillingItemInput],
        discount_rate_or_amount: Optional[Decimal] = None,
        tax_code: Optional[str] = None,
    ) -> TaxCalculationResult:
        pass


class DefaultTaxDiscountService(TaxDiscountServiceInterface):
    """
    Standard deterministic implementation of tax and discount calculation
    matching Member 3's financial contract.
    """

    def calculate_totals(
        self,
        items: List[BillingItemInput],
        discount_rate_or_amount: Optional[Decimal] = None,
        tax_code: Optional[str] = None,
    ) -> TaxCalculationResult:
        subtotal = sum(item.unit_price * item.quantity for item in items)
        
        # Calculate discount
        discount_total = Decimal("0.00")
        if discount_rate_or_amount:
            if discount_rate_or_amount < Decimal("1.00") and discount_rate_or_amount > Decimal("0.00"):
                # Treated as percentage (e.g. 0.10 = 10%)
                discount_total = (subtotal * discount_rate_or_amount).quantize(Decimal("0.01"))
            else:
                discount_total = min(discount_rate_or_amount, subtotal).quantize(Decimal("0.01"))

        taxable_amount = max(Decimal("0.00"), subtotal - discount_total)
        
        # Calculate tax (e.g. GST 18% if GST_18, or 0% default)
        tax_rate = Decimal("0.00")
        if tax_code == "GST_18" or tax_code == "GST18":
            tax_rate = Decimal("0.18")
        elif tax_code == "GST_12" or tax_code == "GST12":
            tax_rate = Decimal("0.12")
        elif tax_code == "GST_5" or tax_code == "GST5":
            tax_rate = Decimal("0.05")
        elif tax_code == "VAT_20" or tax_code == "VAT20":
            tax_rate = Decimal("0.20")

        tax_total = (taxable_amount * tax_rate).quantize(Decimal("0.01"))
        grand_total = (taxable_amount + tax_total).quantize(Decimal("0.01"))

        return TaxCalculationResult(
            subtotal=subtotal.quantize(Decimal("0.01")),
            discount_total=discount_total,
            tax_total=tax_total,
            grand_total=grand_total,
            tax_breakdown={tax_code or "STANDARD": tax_total} if tax_total > 0 else {},
        )
