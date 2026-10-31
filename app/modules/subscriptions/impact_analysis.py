import uuid
from decimal import Decimal
from typing import List
from sqlalchemy.orm import Session

from app.modules.products.models import Product
from app.modules.plans.models import SubscriptionPlan
from app.modules.subscriptions.models import Subscription, SubscriptionItem
from app.modules.quotations.models import Quotation, QuotationItem
from app.modules.subscriptions.schemas import (
    ProductImpactRequest,
    ProductImpactResponse,
    PlanImpactRequest,
    PlanImpactResponse,
    AffectedSubscriptionInfo,
    AffectedQuotationInfo,
)
from app.core.exceptions import EntityNotFoundException


class ChangeImpactService:
    @staticmethod
    def analyze_product_impact(db: Session, org_id: uuid.UUID, data: ProductImpactRequest) -> ProductImpactResponse:
        product = (
            db.query(Product)
            .filter(Product.organization_id == org_id, Product.id == data.product_id)
            .first()
        )
        if not product:
            raise EntityNotFoundException("Product", str(data.product_id))

        # Query active subscriptions containing this product
        sub_items = (
            db.query(SubscriptionItem)
            .join(Subscription, SubscriptionItem.subscription_id == Subscription.id)
            .filter(
                Subscription.organization_id == org_id,
                SubscriptionItem.product_id == product.id,
                Subscription.status.in_(["ACTIVE", "PAUSED"]),
            )
            .all()
        )

        affected_subs: List[AffectedSubscriptionInfo] = []
        total_revenue_protected = Decimal("0.00")

        for item in sub_items:
            sub = item.subscription
            contracted_price = item.unit_price_snapshot
            total_revenue_protected += (contracted_price * item.quantity).quantize(Decimal("0.01"))
            affected_subs.append(
                AffectedSubscriptionInfo(
                    subscription_id=sub.id,
                    subscription_number=sub.subscription_number,
                    customer_id=sub.customer_id,
                    contracted_unit_price=contracted_price,
                    proposed_unit_price=data.proposed_sales_price,
                    status=sub.status,
                    retains_contract_price=True,
                )
            )

        # Query pending quotations containing this product
        q_items = (
            db.query(QuotationItem)
            .join(Quotation, QuotationItem.quotation_id == Quotation.id)
            .filter(
                Quotation.organization_id == org_id,
                QuotationItem.product_id == product.id,
                Quotation.status.in_(["DRAFT", "CONFIRMED"]),
            )
            .all()
        )

        affected_quotes: List[AffectedQuotationInfo] = []
        for q_item in q_items:
            q = q_item.quotation
            affected_quotes.append(
                AffectedQuotationInfo(
                    quotation_id=q.id,
                    quotation_number=q.quotation_number,
                    status=q.status,
                    current_snapshot_price=q_item.unit_price,
                    proposed_price=data.proposed_sales_price,
                )
            )

        deact_note = ""
        if data.proposed_status and data.proposed_status.upper() in ["INACTIVE", "ARCHIVED"]:
            deact_note = " Deactivating this product will prevent new quotations and subscriptions, while existing active subscriptions will continue uninterrupted."

        policy_notice = (
            f"All {len(affected_subs)} existing customer contracts retain their agreed snapshot price. "
            f"Contractual revenue of ₹{total_revenue_protected} is protected and will not be altered.{deact_note}"
        )

        return ProductImpactResponse(
            product_id=product.id,
            product_name=product.name,
            current_sales_price=product.sales_price,
            proposed_sales_price=data.proposed_sales_price,
            current_status=product.status,
            proposed_status=data.proposed_status,
            active_subscriptions_count=len(affected_subs),
            contractual_monthly_revenue_protected=total_revenue_protected,
            affected_active_subscriptions=affected_subs,
            pending_quotations_count=len(affected_quotes),
            affected_quotations=affected_quotes,
            business_policy_notice=policy_notice,
        )

    @staticmethod
    def analyze_plan_impact(db: Session, org_id: uuid.UUID, data: PlanImpactRequest) -> PlanImpactResponse:
        plan = (
            db.query(SubscriptionPlan)
            .filter(SubscriptionPlan.organization_id == org_id, SubscriptionPlan.id == data.plan_id)
            .first()
        )
        if not plan:
            raise EntityNotFoundException("SubscriptionPlan", str(data.plan_id))

        # Query active subscriptions on this plan
        active_subs = (
            db.query(Subscription)
            .filter(
                Subscription.organization_id == org_id,
                Subscription.plan_id == plan.id,
                Subscription.status.in_(["ACTIVE", "PAUSED"]),
            )
            .all()
        )

        affected_subs: List[AffectedSubscriptionInfo] = []
        total_revenue_protected = Decimal("0.00")

        for sub in active_subs:
            sub_recurring = sum((it.unit_price_snapshot * it.quantity for it in sub.items), Decimal("0.00"))
            total_revenue_protected += sub_recurring
            affected_subs.append(
                AffectedSubscriptionInfo(
                    subscription_id=sub.id,
                    subscription_number=sub.subscription_number,
                    customer_id=sub.customer_id,
                    contracted_unit_price=sub_recurring,
                    proposed_unit_price=data.proposed_plan_price,
                    status=sub.status,
                    retains_contract_price=True,
                )
            )

        # Query pending quotations referencing this plan
        q_items = (
            db.query(QuotationItem)
            .join(Quotation, QuotationItem.quotation_id == Quotation.id)
            .filter(
                Quotation.organization_id == org_id,
                QuotationItem.plan_id == plan.id,
                Quotation.status.in_(["DRAFT", "CONFIRMED"]),
            )
            .all()
        )

        affected_quotes: List[AffectedQuotationInfo] = []
        for q_item in q_items:
            q = q_item.quotation
            affected_quotes.append(
                AffectedQuotationInfo(
                    quotation_id=q.id,
                    quotation_number=q.quotation_number,
                    status=q.status,
                    current_snapshot_price=q_item.unit_price,
                    proposed_price=data.proposed_plan_price,
                )
            )

        deact_note = ""
        if data.proposed_status and data.proposed_status.upper() in ["ARCHIVED", "INACTIVE"]:
            deact_note = " Deactivating this plan will block new subscriber intake; existing subscribers remain on current terms until end of billing cycle."

        policy_notice = (
            f"All {len(affected_subs)} existing subscriptions on plan '{plan.name}' retain their locked contractual pricing. "
            f"Total recurring revenue of ₹{total_revenue_protected} remains protected.{deact_note}"
        )

        return PlanImpactResponse(
            plan_id=plan.id,
            plan_name=plan.name,
            current_plan_price=plan.plan_price,
            proposed_plan_price=data.proposed_plan_price,
            current_status=plan.status,
            proposed_status=data.proposed_status,
            active_subscriptions_count=len(affected_subs),
            contractual_revenue_protected=total_revenue_protected,
            affected_active_subscriptions=affected_subs,
            pending_quotations_count=len(affected_quotes),
            affected_quotations=affected_quotes,
            business_policy_notice=policy_notice,
        )
