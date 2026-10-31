"""Repository layer for customer data access."""

import uuid
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from app.modules.customers.models import Customer, CustomerStatus


class CustomerRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, org_id: uuid.UUID, customer_id: uuid.UUID) -> Optional[Customer]:
        return (
            self.db.query(Customer)
            .filter(Customer.organization_id == org_id, Customer.id == customer_id)
            .first()
        )

    def get_by_code(self, org_id: uuid.UUID, customer_code: str, exclude_id: Optional[uuid.UUID] = None) -> Optional[Customer]:
        q = self.db.query(Customer).filter(
            Customer.organization_id == org_id,
            Customer.customer_code == customer_code,
        )
        if exclude_id:
            q = q.filter(Customer.id != exclude_id)
        return q.first()

    def get_by_email(self, org_id: uuid.UUID, email: str, exclude_id: Optional[uuid.UUID] = None) -> Optional[Customer]:
        q = self.db.query(Customer).filter(
            Customer.organization_id == org_id,
            Customer.email == email,
        )
        if exclude_id:
            q = q.filter(Customer.id != exclude_id)
        return q.first()

    def list(
        self,
        org_id: uuid.UUID,
        search: Optional[str] = None,
        status: Optional[CustomerStatus] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[Customer], int]:
        query = self.db.query(Customer).filter(Customer.organization_id == org_id)
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Customer.company_name.ilike(search_term),
                    Customer.contact_name.ilike(search_term),
                    Customer.email.ilike(search_term),
                    Customer.customer_code.ilike(search_term),
                )
            )
        if status:
            query = query.filter(Customer.status == status)

        total = query.with_entities(func.count(Customer.id)).scalar() or 0
        customers = query.order_by(Customer.created_at.desc()).offset(skip).limit(limit).all()
        return customers, total

    def save(self, customer: Customer) -> Customer:
        self.db.add(customer)
        self.db.commit()
        self.db.refresh(customer)
        return customer

    def delete(self, customer: Customer) -> None:
        self.db.delete(customer)
        self.db.commit()
