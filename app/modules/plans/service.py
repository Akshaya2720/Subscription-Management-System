import uuid
from decimal import Decimal
from datetime import datetime, date, timezone
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session

from app.modules.plans.models import SubscriptionPlan, PlanPriceHistory
from app.modules.plans.repository import PlanRepository
from app.modules.plans.schemas import PlanCreate, PlanUpdate
from app.core.exceptions import (
    EntityNotFoundException,
    DuplicateEntityException,
    BusinessRuleValidationException,
)


class PlanService:
    @staticmethod
    def create_plan(db: Session, org_id: uuid.UUID, data: PlanCreate) -> SubscriptionPlan:
        repo = PlanRepository(db)
        if repo.get_by_name(org_id, data.name):
            raise DuplicateEntityException(f"Subscription plan '{data.name}' already exists.")

        # Determine boolean flags from configuration or defaults
        auto_close = bool(data.auto_close_configuration and data.auto_close_configuration.get("enabled", False))
        closable_early = bool(data.early_closure_configuration is None or data.early_closure_configuration.get("allowed", True))
        pausable = bool(data.pause_configuration is None or data.pause_configuration.get("allowed", True))
        renewable = bool(data.renewal_configuration is None or data.renewal_configuration.get("allowed", True))

        plan = SubscriptionPlan(
            organization_id=org_id,
            name=data.name,
            description=data.description,
            billing_frequency=data.billing_frequency.value,
            plan_price=data.plan_price,
            minimum_quantity=data.minimum_quantity,
            start_availability_date=data.start_availability_date,
            end_availability_date=data.end_availability_date,
            is_auto_close_at_end=auto_close,
            is_closable_early=closable_early,
            is_pausable=pausable,
            is_renewable=renewable,
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
        repo = PlanRepository(db)
        plan = repo.get_by_id(org_id, plan_id)
        if not plan:
            raise EntityNotFoundException("SubscriptionPlan", str(plan_id))
        return plan

    @staticmethod
    def update_plan(db: Session, org_id: uuid.UUID, plan_id: uuid.UUID, data: PlanUpdate) -> SubscriptionPlan:
        repo = PlanRepository(db)
        plan = PlanService.get_plan(db, org_id, plan_id)

        if data.name and data.name != plan.name:
            if repo.get_by_name(org_id, data.name, exclude_id=plan_id):
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
            if key not in ("name", "plan_price") and value is not None:
                setattr(plan, key, value)

        if data.auto_close_configuration is not None:
            plan.is_auto_close_at_end = bool(data.auto_close_configuration.get("enabled", False))
        if data.early_closure_configuration is not None:
            plan.is_closable_early = bool(data.early_closure_configuration.get("allowed", True))
        if data.pause_configuration is not None:
            plan.is_pausable = bool(data.pause_configuration.get("allowed", True))
        if data.renewal_configuration is not None:
            plan.is_renewable = bool(data.renewal_configuration.get("allowed", True))

        db.commit()
        db.refresh(plan)
        return plan

    @staticmethod
    def list_plans(
        db: Session,
        org_id: uuid.UUID,
        search: Optional[str] = None,
        billing_frequency: Optional[str] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[SubscriptionPlan], int]:
        repo = PlanRepository(db)
        return repo.list(org_id, search=search, billing_frequency=billing_frequency, status=status, skip=skip, limit=limit)

    @staticmethod
    def get_plan_price_history(db: Session, org_id: uuid.UUID, plan_id: uuid.UUID) -> List[PlanPriceHistory]:
        PlanService.get_plan(db, org_id, plan_id)
        repo = PlanRepository(db)
        return repo.get_price_history(plan_id)

    get_price_history = get_plan_price_history

    @staticmethod
    def validate_plan_availability(plan: SubscriptionPlan, target_date: Optional[date] = None) -> bool:
        check_date = target_date or date.today()
        if plan.status != "ACTIVE":
            return False
        if plan.start_availability_date and check_date < plan.start_availability_date:
            return False
        if plan.end_availability_date and check_date > plan.end_availability_date:
            return False
        return True
