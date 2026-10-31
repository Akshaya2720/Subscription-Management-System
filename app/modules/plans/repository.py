"""Repository layer for subscription plans and price history."""

import uuid
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.modules.plans.models import SubscriptionPlan, PlanPriceHistory


class PlanRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, org_id: uuid.UUID, plan_id: uuid.UUID) -> Optional[SubscriptionPlan]:
        return (
            self.db.query(SubscriptionPlan)
            .filter(SubscriptionPlan.organization_id == org_id, SubscriptionPlan.id == plan_id)
            .first()
        )

    def get_by_name(self, org_id: uuid.UUID, name: str, exclude_id: Optional[uuid.UUID] = None) -> Optional[SubscriptionPlan]:
        q = self.db.query(SubscriptionPlan).filter(
            SubscriptionPlan.organization_id == org_id,
            SubscriptionPlan.name == name,
        )
        if exclude_id:
            q = q.filter(SubscriptionPlan.id != exclude_id)
        return q.first()

    def list(
        self,
        org_id: uuid.UUID,
        search: Optional[str] = None,
        billing_frequency: Optional[str] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[SubscriptionPlan], int]:
        query = self.db.query(SubscriptionPlan).filter(SubscriptionPlan.organization_id == org_id)
        if search:
            query = query.filter(
                or_(
                    SubscriptionPlan.name.ilike(f"%{search}%"),
                    SubscriptionPlan.description.ilike(f"%{search}%"),
                )
            )
        if billing_frequency:
            query = query.filter(SubscriptionPlan.billing_frequency == billing_frequency)
        if status:
            query = query.filter(SubscriptionPlan.status == status)

        total = query.count()
        plans = query.order_by(SubscriptionPlan.name.asc()).offset(skip).limit(limit).all()
        return plans, total

    def save(self, plan: SubscriptionPlan) -> SubscriptionPlan:
        self.db.add(plan)
        self.db.commit()
        self.db.refresh(plan)
        return plan

    def add_price_history(self, history: PlanPriceHistory) -> PlanPriceHistory:
        self.db.add(history)
        self.db.commit()
        self.db.refresh(history)
        return history

    def get_price_history(self, plan_id: uuid.UUID) -> List[PlanPriceHistory]:
        return (
            self.db.query(PlanPriceHistory)
            .filter(PlanPriceHistory.plan_id == plan_id)
            .order_by(PlanPriceHistory.effective_from.desc())
            .all()
        )
