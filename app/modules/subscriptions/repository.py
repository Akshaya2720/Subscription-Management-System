"""Repository layer for subscriptions, subscription items, and subscription events."""

import uuid
from datetime import date
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session, selectinload

from app.modules.subscriptions.models import Subscription, SubscriptionItem, SubscriptionEvent


class SubscriptionRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, org_id: uuid.UUID, subscription_id: uuid.UUID) -> Optional[Subscription]:
        return (
            self.db.query(Subscription)
            .options(selectinload(Subscription.items))
            .filter(Subscription.organization_id == org_id, Subscription.id == subscription_id)
            .first()
        )

    def get_by_number(self, org_id: uuid.UUID, subscription_number: str) -> Optional[Subscription]:
        return (
            self.db.query(Subscription)
            .options(selectinload(Subscription.items))
            .filter(Subscription.organization_id == org_id, Subscription.subscription_number == subscription_number)
            .first()
        )

    def list(
        self,
        org_id: uuid.UUID,
        customer_id: Optional[uuid.UUID] = None,
        plan_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> Tuple[List[Subscription], int]:
        query = self.db.query(Subscription).filter(Subscription.organization_id == org_id)
        if customer_id:
            query = query.filter(Subscription.customer_id == customer_id)
        if plan_id:
            query = query.filter(Subscription.plan_id == plan_id)
        if status:
            query = query.filter(Subscription.status == status.upper())

        total = query.count()
        items = (
            query.options(selectinload(Subscription.items))
            .order_by(Subscription.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        return items, total

    def get_due_for_billing(self, org_id: uuid.UUID, as_of_date: date) -> List[Subscription]:
        """Find active subscriptions due for recurring billing with items eagerly loaded."""
        return (
            self.db.query(Subscription)
            .options(selectinload(Subscription.items))
            .filter(
                Subscription.organization_id == org_id,
                Subscription.status == "ACTIVE",
                Subscription.next_billing_date <= as_of_date,
            )
            .all()
        )

    def save(self, subscription: Subscription) -> Subscription:
        self.db.add(subscription)
        self.db.commit()
        self.db.refresh(subscription)
        return subscription

    def log_event(self, event: SubscriptionEvent) -> SubscriptionEvent:
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def get_events(self, subscription_id: uuid.UUID) -> List[SubscriptionEvent]:
        return (
            self.db.query(SubscriptionEvent)
            .filter(SubscriptionEvent.subscription_id == subscription_id)
            .order_by(SubscriptionEvent.created_at.asc())
            .all()
        )
