import uuid
import random
from decimal import Decimal
from datetime import datetime, date, timezone
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.modules.subscriptions.models import Subscription, SubscriptionItem, SubscriptionEvent
from app.modules.subscriptions.schemas import (
    SubscriptionCreate,
    SubscriptionUpdate,
    SubscriptionPauseRequest,
    SubscriptionResumeRequest,
    SubscriptionRenewRequest,
    SubscriptionCloseRequest,
)
from app.modules.subscriptions.lifecycle import SubscriptionLifecycleManager
from app.modules.customers.service import CustomerService
from app.modules.plans.service import PlanService
from app.modules.products.models import Product, ProductVariant
from app.modules.quotations.models import Quotation
from app.core.exceptions import (
    EntityNotFoundException,
    DuplicateEntityException,
    InvalidStateTransitionException,
    BusinessRuleValidationException,
)


class SubscriptionService:
    @staticmethod
    def _generate_subscription_number() -> str:
        today_str = datetime.now().strftime("%Y%m%d")
        rand_num = random.randint(1000, 9999)
        return f"SUB-{today_str}-{rand_num}"

    @staticmethod
    def log_event(
        db: Session,
        subscription_id: uuid.UUID,
        event_type: str,
        previous_status: Optional[str],
        new_status: Optional[str],
        description: str,
        metadata_json: Optional[dict] = None,
    ) -> SubscriptionEvent:
        event = SubscriptionEvent(
            subscription_id=subscription_id,
            event_type=event_type,
            previous_status=previous_status,
            new_status=new_status,
            description=description,
            metadata_json=metadata_json or {},
        )
        db.add(event)
        return event

    @staticmethod
    def create_subscription(db: Session, org_id: uuid.UUID, data: SubscriptionCreate) -> Subscription:
        # 1. Validate Customer
        CustomerService.get_customer(db, org_id, data.customer_id)

        # 2. Validate Plan
        plan = PlanService.get_plan(db, org_id, data.plan_id)
        PlanService.validate_plan_availability(plan, data.start_date)

        # Calculate minimum quantity
        total_quantity = sum(item.quantity for item in data.items)
        if total_quantity < plan.minimum_quantity:
            raise BusinessRuleValidationException(
                f"Total subscription quantity ({total_quantity}) is below minimum quantity required ({plan.minimum_quantity}) for plan '{plan.name}'."
            )

        freq = (data.billing_frequency or plan.billing_frequency).upper()
        start = data.start_date or date.today()
        next_billing = SubscriptionLifecycleManager.calculate_next_billing_date(start, freq)

        sub_num = data.subscription_number or SubscriptionService._generate_subscription_number()
        existing = (
            db.query(Subscription)
            .filter(Subscription.organization_id == org_id, Subscription.subscription_number == sub_num)
            .first()
        )
        if existing:
            sub_num = SubscriptionService._generate_subscription_number()

        subscription = Subscription(
            organization_id=org_id,
            customer_id=data.customer_id,
            plan_id=plan.id,
            quotation_id=data.quotation_id,
            subscription_number=sub_num,
            start_date=start,
            next_billing_date=next_billing,
            billing_frequency=freq,
            payment_terms=data.payment_terms,
            status="DRAFT",
            currency=data.currency,
            renewal_enabled=data.renewal_enabled,
        )
        db.add(subscription)
        db.flush()

        # Build items with pricing snapshots
        for it in data.items:
            product = (
                db.query(Product)
                .filter(Product.organization_id == org_id, Product.id == it.product_id)
                .first()
            )
            if not product:
                raise EntityNotFoundException("Product", str(it.product_id))

            variant = None
            if it.variant_id:
                variant = (
                    db.query(ProductVariant)
                    .filter(ProductVariant.product_id == product.id, ProductVariant.id == it.variant_id)
                    .first()
                )
                if not variant:
                    raise EntityNotFoundException("ProductVariant", str(it.variant_id))

            if it.unit_price_snapshot is not None:
                unit_price = it.unit_price_snapshot
            else:
                unit_price = product.sales_price + (variant.additional_price if variant else Decimal("0.00"))

            desc = it.description_snapshot
            if not desc:
                desc = product.name + (f" ({variant.variant_name})" if variant else "")

            line_total = (unit_price * it.quantity).quantize(Decimal("0.01"))

            sub_item = SubscriptionItem(
                subscription_id=subscription.id,
                product_id=product.id,
                variant_id=variant.id if variant else None,
                description_snapshot=desc,
                quantity=it.quantity,
                unit_price_snapshot=unit_price,
                line_total=line_total,
            )
            db.add(sub_item)

        SubscriptionService.log_event(
            db,
            subscription_id=subscription.id,
            event_type="CREATED",
            previous_status=None,
            new_status="DRAFT",
            description=f"Subscription {subscription.subscription_number} created in DRAFT.",
        )

        db.commit()
        db.refresh(subscription)
        return subscription

    @staticmethod
    def create_from_quotation(
        db: Session, org_id: uuid.UUID, quotation: Quotation, payload
    ) -> Subscription:
        # Determine plan
        plan_id = payload.plan_id
        if not plan_id:
            # Check quotation items for a plan reference
            for item in quotation.items:
                if item.plan_id:
                    plan_id = item.plan_id
                    break
        if not plan_id:
            # Pick first active plan in org
            first_plan = (
                db.query(SubscriptionPlan)
                .filter(SubscriptionPlan.organization_id == org_id, SubscriptionPlan.status == "ACTIVE")
                .first()
            )
            if not first_plan:
                raise BusinessRuleValidationException("No active subscription plan found in organization.")
            plan_id = first_plan.id

        plan = PlanService.get_plan(db, org_id, plan_id)
        start = payload.start_date or date.today()
        freq = (payload.billing_frequency or plan.billing_frequency).upper()
        next_billing = SubscriptionLifecycleManager.calculate_next_billing_date(start, freq)

        sub_num = SubscriptionService._generate_subscription_number()

        subscription = Subscription(
            organization_id=org_id,
            customer_id=quotation.customer_id,
            plan_id=plan.id,
            quotation_id=quotation.id,
            subscription_number=sub_num,
            start_date=start,
            next_billing_date=next_billing,
            billing_frequency=freq,
            payment_terms=payload.payment_terms,
            status="CONFIRMED",
            currency=payload.currency,
            renewal_enabled=True,
        )
        db.add(subscription)
        db.flush()

        # Copy quotation items as subscription items with immutable snapshots
        for q_item in quotation.items:
            sub_item = SubscriptionItem(
                subscription_id=subscription.id,
                product_id=q_item.product_id,
                variant_id=q_item.variant_id,
                description_snapshot=q_item.description,
                quantity=q_item.quantity,
                unit_price_snapshot=q_item.unit_price,
                line_total=q_item.line_total,
            )
            db.add(sub_item)

        SubscriptionService.log_event(
            db,
            subscription_id=subscription.id,
            event_type="QUOTATION_CONVERTED",
            previous_status="DRAFT",
            new_status="CONFIRMED",
            description=f"Subscription generated from confirmed quotation {quotation.quotation_number}.",
            metadata_json={"quotation_id": str(quotation.id), "quotation_number": quotation.quotation_number},
        )

        db.commit()
        db.refresh(subscription)
        return subscription

    @staticmethod
    def get_subscription(db: Session, org_id: uuid.UUID, subscription_id: uuid.UUID) -> Subscription:
        sub = (
            db.query(Subscription)
            .filter(Subscription.organization_id == org_id, Subscription.id == subscription_id)
            .first()
        )
        if not sub:
            raise EntityNotFoundException("Subscription", str(subscription_id))
        return sub

    @staticmethod
    def activate_subscription(db: Session, org_id: uuid.UUID, subscription_id: uuid.UUID) -> Subscription:
        sub = SubscriptionService.get_subscription(db, org_id, subscription_id)
        
        # Validated state transition
        SubscriptionLifecycleManager.validate_transition(sub.status, "ACTIVE", sub.expiry_date)

        old_status = sub.status
        sub.status = "ACTIVE"
        if not sub.next_billing_date or sub.next_billing_date < date.today():
            sub.next_billing_date = SubscriptionLifecycleManager.calculate_next_billing_date(
                date.today(), sub.billing_frequency
            )

        SubscriptionService.log_event(
            db,
            subscription_id=sub.id,
            event_type="ACTIVATED",
            previous_status=old_status,
            new_status="ACTIVE",
            description=f"Subscription {sub.subscription_number} activated. Next billing date: {sub.next_billing_date}.",
        )
        db.commit()
        db.refresh(sub)
        return sub

    @staticmethod
    def pause_subscription(
        db: Session, org_id: uuid.UUID, subscription_id: uuid.UUID, payload: SubscriptionPauseRequest
    ) -> Subscription:
        sub = SubscriptionService.get_subscription(db, org_id, subscription_id)
        if sub.status != "ACTIVE":
            raise InvalidStateTransitionException(
                current_status=sub.status,
                target_status="PAUSED",
                reason=f"Cannot pause subscription in '{sub.status}' status. Only ACTIVE subscriptions can be paused.",
            )
        SubscriptionLifecycleManager.validate_transition(sub.status, "PAUSED")

        old_status = sub.status
        sub.status = "PAUSED"
        sub.pause_information = {
            "paused_at": datetime.now(timezone.utc).isoformat(),
            "reason": payload.reason,
            "resume_date": payload.resume_date.isoformat() if payload.resume_date else None,
        }

        SubscriptionService.log_event(
            db,
            subscription_id=sub.id,
            event_type="PAUSED",
            previous_status=old_status,
            new_status="PAUSED",
            description=f"Subscription paused. Reason: {payload.reason}.",
            metadata_json=sub.pause_information,
        )
        db.commit()
        db.refresh(sub)
        return sub

    @staticmethod
    def resume_subscription(
        db: Session, org_id: uuid.UUID, subscription_id: uuid.UUID, payload: SubscriptionResumeRequest
    ) -> Subscription:
        sub = SubscriptionService.get_subscription(db, org_id, subscription_id)
        if sub.status != "PAUSED":
            raise InvalidStateTransitionException(
                current_status=sub.status,
                target_status="ACTIVE",
                reason=f"Cannot resume subscription in '{sub.status}' status. Only PAUSED subscriptions can be resumed.",
            )
        SubscriptionLifecycleManager.validate_transition(sub.status, "ACTIVE")

        old_status = sub.status
        sub.status = "ACTIVE"
        prev_pause = sub.pause_information or {}
        sub.pause_information = None

        SubscriptionService.log_event(
            db,
            subscription_id=sub.id,
            event_type="RESUMED",
            previous_status=old_status,
            new_status="ACTIVE",
            description="Subscription resumed from pause.",
            metadata_json={"resumed_from": prev_pause, "notes": payload.notes},
        )
        db.commit()
        db.refresh(sub)
        return sub

    @staticmethod
    def renew_subscription(
        db: Session, org_id: uuid.UUID, subscription_id: uuid.UUID, payload: SubscriptionRenewRequest
    ) -> Subscription:
        sub = SubscriptionService.get_subscription(db, org_id, subscription_id)
        
        if sub.status not in ["ACTIVE"]:
            raise InvalidStateTransitionException(
                current_status=sub.status,
                target_status="ACTIVE",
                reason=f"Cannot renew subscription in '{sub.status}' status. Only ACTIVE subscriptions can be renewed.",
            )

        if not sub.renewal_enabled:
            raise BusinessRuleValidationException("Subscription has renewal disabled.")

        new_billing, new_expiry = SubscriptionLifecycleManager.calculate_renewal_dates(
            current_expiry=sub.expiry_date,
            current_next_billing=sub.next_billing_date,
            frequency=sub.billing_frequency,
            periods=payload.extension_periods,
        )

        old_next_billing = sub.next_billing_date
        old_expiry = sub.expiry_date

        sub.next_billing_date = new_billing
        sub.expiry_date = new_expiry

        SubscriptionService.log_event(
            db,
            subscription_id=sub.id,
            event_type="RENEWED",
            previous_status="ACTIVE",
            new_status="ACTIVE",
            description=f"Subscription renewed for {payload.extension_periods} period(s).",
            metadata_json={
                "previous_next_billing_date": str(old_next_billing),
                "new_next_billing_date": str(new_billing),
                "previous_expiry_date": str(old_expiry) if old_expiry else None,
                "new_expiry_date": str(new_expiry) if new_expiry else None,
            },
        )
        db.commit()
        db.refresh(sub)
        return sub

    @staticmethod
    def close_subscription(
        db: Session, org_id: uuid.UUID, subscription_id: uuid.UUID, payload: SubscriptionCloseRequest
    ) -> Subscription:
        sub = SubscriptionService.get_subscription(db, org_id, subscription_id)
        SubscriptionLifecycleManager.validate_transition(sub.status, "CLOSED")

        old_status = sub.status
        sub.status = "CLOSED"
        sub.closure_information = {
            "closed_at": datetime.now(timezone.utc).isoformat(),
            "reason": payload.reason,
            "early_closure_fee": str(payload.early_closure_fee) if payload.early_closure_fee else "0.00",
        }

        SubscriptionService.log_event(
            db,
            subscription_id=sub.id,
            event_type="CLOSED",
            previous_status=old_status,
            new_status="CLOSED",
            description=f"Subscription closed. Reason: {payload.reason}.",
            metadata_json=sub.closure_information,
        )
        db.commit()
        db.refresh(sub)
        return sub

    @staticmethod
    def update_subscription(
        db: Session, org_id: uuid.UUID, subscription_id: uuid.UUID, data: SubscriptionUpdate
    ) -> Subscription:
        sub = SubscriptionService.get_subscription(db, org_id, subscription_id)

        update_dict = data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(sub, key, value)

        SubscriptionService.log_event(
            db,
            subscription_id=sub.id,
            event_type="UPDATED",
            previous_status=sub.status,
            new_status=sub.status,
            description="Subscription metadata updated.",
            metadata_json=update_dict,
        )
        db.commit()
        db.refresh(sub)
        return sub

    @staticmethod
    def list_subscriptions(
        db: Session,
        org_id: uuid.UUID,
        customer_id: Optional[uuid.UUID] = None,
        plan_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> Tuple[List[Subscription], int]:
        query = db.query(Subscription).filter(Subscription.organization_id == org_id)

        if customer_id:
            query = query.filter(Subscription.customer_id == customer_id)

        if plan_id:
            query = query.filter(Subscription.plan_id == plan_id)

        if status:
            query = query.filter(Subscription.status == status.upper())

        if search:
            query = query.filter(Subscription.subscription_number.ilike(f"%{search}%"))

        total = query.count()
        items = query.order_by(Subscription.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
        return items, total

    @staticmethod
    def get_events(db: Session, org_id: uuid.UUID, subscription_id: uuid.UUID) -> List[SubscriptionEvent]:
        SubscriptionService.get_subscription(db, org_id, subscription_id)
        return (
            db.query(SubscriptionEvent)
            .filter(SubscriptionEvent.subscription_id == subscription_id)
            .order_by(SubscriptionEvent.created_at.desc())
            .all()
        )
