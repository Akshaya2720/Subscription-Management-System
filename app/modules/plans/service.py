import uuid
from decimal import Decimal
from datetime import datetime, date, timezone
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.modules.plans.models import SubscriptionPlan, PlanPriceHistory
from app.modules.plans.schemas import PlanCreate, PlanUpdate
from app.core.exceptions import (
    EntityNotFoundException,
    DuplicateEntityException,
    BusinessRuleValidationException,
)


class PlanService:
    @staticmethod
    def create_plan(db: Session, org_id: uuid.UUID, data: PlanCreate) -> SubscriptionPlan:
        existing = (
            db.query(SubscriptionPlan)
            .filter(SubscriptionPlan.organization_id == org_id, SubscriptionPlan.name == data.name)
            .first()
        )
        if existing:
            raise DuplicateEntityException(f"Subscription plan '{data.name}' already exists.")

        plan = SubscriptionPlan(
            organization_id=org_id,
            name=data.name,
            description=data.description,
            billing_frequency=data.billing_frequency.value,
            plan_price=data.plan_price,
            minimum_quantity=data.minimum_quantity,
            start_availability_date=data.start_availability_date,
            end_availability_date=data.end_availability_date,
            auto_close_configuration=data.auto_close_configuration or {},
            early_closure_configuration=data.early_closure_configuration or {},
            pause_configuration=data.pause_configuration or {},
            renewal_configuration=data.renewal_configuration or {},
            status=data.status,
        )
        db.add(plan)
        db.flush()

        # Record initial price history
        initial_history = PlanPriceHistory(
            plan_id=plan.id,
            price=plan.plan_price,
            effective_from=datetime.now(timezone.utc),
            notes="Initial plan price",
        )
        db.add(initial_history)
        db.commit()
        db.refresh(plan)
        return plan

    @staticmethod
    def get_plan(db: Session, org_id: uuid.UUID, plan_id: uuid.UUID) -> SubscriptionPlan:
        plan = (
            db.query(SubscriptionPlan)
            .filter(SubscriptionPlan.organization_id == org_id, SubscriptionPlan.id == plan_id)
            .first()
        )
        if not plan:
            raise EntityNotFoundException("SubscriptionPlan", str(plan_id))
        return plan

    @staticmethod
    def update_plan(db: Session, org_id: uuid.UUID, plan_id: uuid.UUID, data: PlanUpdate) -> SubscriptionPlan:
        plan = PlanService.get_plan(db, org_id, plan_id)

        if data.name and data.name != plan.name:
            existing = (
                db.query(SubscriptionPlan)
                .filter(
                    SubscriptionPlan.organization_id == org_id,
                    SubscriptionPlan.name == data.name,
                    SubscriptionPlan.id != plan_id,
                )
                .first()
            )
            if existing:
                raise DuplicateEntityException(f"Plan name '{data.name}' already in use.")
            plan.name = data.name

        # Check for price update
        if data.plan_price is not None and data.plan_price != plan.plan_price:
            old_price = plan.plan_price
            plan.plan_price = data.plan_price
            history = PlanPriceHistory(
                plan_id=plan.id,
                price=data.plan_price,
                effective_from=datetime.now(timezone.utc),
                notes=f"Price revised from {old_price} to {data.plan_price}",
            )
            db.add(history)

        update_dict = data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            if key not in ("name", "plan_price", "billing_frequency") and value is not None:
                setattr(plan, key, value)
            elif key == "billing_frequency" and value is not None:
                plan.billing_frequency = value.value

        db.commit()
        db.refresh(plan)
        return plan

    @staticmethod
    def delete_or_archive_plan(db: Session, org_id: uuid.UUID, plan_id: uuid.UUID) -> SubscriptionPlan:
        plan = PlanService.get_plan(db, org_id, plan_id)
        plan.status = "ARCHIVED"
        db.commit()
        db.refresh(plan)
        return plan

    @staticmethod
    def list_plans(
        db: Session,
        org_id: uuid.UUID,
        search: Optional[str] = None,
        status: Optional[str] = None,
        frequency: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> Tuple[List[SubscriptionPlan], int]:
        query = db.query(SubscriptionPlan).filter(SubscriptionPlan.organization_id == org_id)

        if status:
            query = query.filter(SubscriptionPlan.status == status.upper())

        if frequency:
            query = query.filter(SubscriptionPlan.billing_frequency == frequency.upper())

        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    SubscriptionPlan.name.ilike(search_pattern),
                    SubscriptionPlan.description.ilike(search_pattern),
                )
            )

        total = query.count()
        items = query.order_by(SubscriptionPlan.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
        return items, total

    @staticmethod
    def validate_plan_availability(plan: SubscriptionPlan, check_date: Optional[date] = None) -> bool:
        """Verify if a plan is currently available for subscription."""
        if plan.status != "ACTIVE":
            raise BusinessRuleValidationException(f"Plan '{plan.name}' is not ACTIVE (status: {plan.status}).")

        target_date = check_date or date.today()
        if plan.start_availability_date and target_date < plan.start_availability_date:
            raise BusinessRuleValidationException(
                f"Plan '{plan.name}' is not yet available. Available from {plan.start_availability_date}."
            )
        if plan.end_availability_date and target_date > plan.end_availability_date:
            raise BusinessRuleValidationException(
                f"Plan '{plan.name}' availability expired on {plan.end_availability_date}."
            )
        return True

    @staticmethod
    def get_price_history(db: Session, org_id: uuid.UUID, plan_id: uuid.UUID) -> List[PlanPriceHistory]:
        plan = PlanService.get_plan(db, org_id, plan_id)
        return (
            db.query(PlanPriceHistory)
            .filter(PlanPriceHistory.plan_id == plan.id)
            .order_by(PlanPriceHistory.created_at.desc())
            .all()
        )
