import uuid
from decimal import Decimal
from typing import List
from sqlalchemy.orm import Session

from app.modules.subscriptions.models import Subscription, SubscriptionItem, SubscriptionEvent
from app.modules.customers.models import Customer
from app.modules.plans.models import SubscriptionPlan
from app.modules.quotations.models import Quotation
from app.modules.billing.models import Invoice, Payment
from app.modules.subscriptions.schemas import (
    DigitalTwinResponse,
    DigitalTwinCustomer,
    DigitalTwinPlan,
    DigitalTwinInvoice,
    DigitalTwinPayment,
    DigitalTwinQuotation,
    SubscriptionItemResponse,
    SubscriptionEventResponse,
)
from app.core.exceptions import EntityNotFoundException


class DigitalTwinService:
    @staticmethod
    def get_digital_twin(db: Session, org_id: uuid.UUID, subscription_id: uuid.UUID) -> DigitalTwinResponse:
        subscription = (
            db.query(Subscription)
            .filter(Subscription.organization_id == org_id, Subscription.id == subscription_id)
            .first()
        )
        if not subscription:
            raise EntityNotFoundException("Subscription", str(subscription_id))

        # 1. Customer actual records
        customer = db.query(Customer).filter(Customer.id == subscription.customer_id).first()
        twin_customer = DigitalTwinCustomer(
            id=customer.id,
            customer_code=customer.customer_code,
            company_name=customer.company_name,
            contact_name=customer.contact_name,
            email=customer.email,
            phone=customer.phone,
            billing_address=customer.billing_address,
            tax_identifier=customer.tax_identifier,
            status=customer.status,
        )

        # 2. Plan actual records
        plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == subscription.plan_id).first()
        twin_plan = DigitalTwinPlan(
            id=plan.id,
            name=plan.name,
            billing_frequency=plan.billing_frequency,
            current_catalog_price=plan.plan_price,
            is_available=(plan.status == "ACTIVE"),
        )

        # 3. Contractual price calculation from subscription items snapshots
        contractual_recurring_price = sum(
            (item.unit_price_snapshot * item.quantity for item in subscription.items),
            Decimal("0.00"),
        )
        total_contract_value = contractual_recurring_price

        # 4. Actual Quotation records
        twin_quotations: List[DigitalTwinQuotation] = []
        if subscription.quotation_id:
            q = db.query(Quotation).filter(Quotation.id == subscription.quotation_id).first()
            if q:
                twin_quotations.append(
                    DigitalTwinQuotation(
                        id=q.id,
                        quotation_number=q.quotation_number,
                        quotation_date=q.quotation_date,
                        expiry_date=q.expiry_date,
                        subtotal=q.subtotal,
                        discount_total=q.discount_total,
                        tax_total=q.tax_total,
                        grand_total=q.grand_total,
                        status=q.status,
                    )
                )

        # 5. Actual Invoice records
        invoices = (
            db.query(Invoice)
            .filter(
                Invoice.organization_id == org_id,
                Invoice.subscription_id == subscription.id,
            )
            .order_by(Invoice.issue_date.desc())
            .all()
        )
        twin_invoices: List[DigitalTwinInvoice] = []
        twin_payments: List[DigitalTwinPayment] = []
        verification_status = "PENDING"

        for inv in invoices:
            twin_invoices.append(
                DigitalTwinInvoice(
                    id=inv.id,
                    invoice_number=inv.invoice_number,
                    issue_date=inv.issue_date,
                    due_date=inv.due_date,
                    subtotal=inv.subtotal,
                    discount_total=inv.discount_total,
                    tax_total=inv.tax_total,
                    total_amount=inv.total_amount,
                    status=inv.status,
                    verification_status=inv.verification_status,
                )
            )
            if inv.verification_status:
                verification_status = inv.verification_status

            # Payments for this invoice
            payments = db.query(Payment).filter(Payment.invoice_id == inv.id).all()
            for pay in payments:
                twin_payments.append(
                    DigitalTwinPayment(
                        id=pay.id,
                        invoice_id=pay.invoice_id,
                        amount=pay.amount,
                        payment_method=pay.payment_method,
                        payment_date=pay.payment_date,
                        transaction_reference=pay.transaction_reference,
                        status=pay.status,
                    )
                )

        # 6. Change history / events
        events = (
            db.query(SubscriptionEvent)
            .filter(SubscriptionEvent.subscription_id == subscription.id)
            .order_by(SubscriptionEvent.created_at.desc())
            .all()
        )
        twin_events = [
            SubscriptionEventResponse(
                id=e.id,
                subscription_id=e.subscription_id,
                event_type=e.event_type,
                previous_status=e.previous_status,
                new_status=e.new_status,
                description=e.description,
                metadata_json=e.metadata_json,
                created_at=e.created_at,
            )
            for e in events
        ]

        twin_items = [
            SubscriptionItemResponse(
                id=it.id,
                subscription_id=it.subscription_id,
                product_id=it.product_id,
                variant_id=it.variant_id,
                description_snapshot=it.description_snapshot,
                quantity=it.quantity,
                unit_price_snapshot=it.unit_price_snapshot,
                line_total=it.line_total,
            )
            for it in subscription.items
        ]

        return DigitalTwinResponse(
            subscription_id=subscription.id,
            subscription_number=subscription.subscription_number,
            status=subscription.status,
            start_date=subscription.start_date,
            next_billing_date=subscription.next_billing_date,
            expiry_date=subscription.expiry_date,
            billing_frequency=subscription.billing_frequency,
            payment_terms=subscription.payment_terms,
            currency=subscription.currency,
            renewal_enabled=subscription.renewal_enabled,
            contractual_recurring_price=contractual_recurring_price,
            total_contract_value=total_contract_value,
            pause_information=subscription.pause_information,
            closure_information=subscription.closure_information,
            customer=twin_customer,
            plan=twin_plan,
            subscription_items=twin_items,
            quotations=twin_quotations,
            invoices=twin_invoices,
            payments=twin_payments,
            subscription_change_history=twin_events,
            verification_status=verification_status,
        )
