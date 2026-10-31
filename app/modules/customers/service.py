import uuid
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, select, func

from app.modules.customers.models import Customer
from app.modules.customers.schemas import CustomerCreate, CustomerUpdate
from app.core.exceptions import EntityNotFoundException, DuplicateEntityException, BusinessRuleValidationException
from app.modules.billing.models import Invoice


class CustomerService:
    @staticmethod
    def create_customer(db: Session, org_id: uuid.UUID, data: CustomerCreate) -> Customer:
        # Check duplicate customer_code in org
        existing_code = (
            db.query(Customer)
            .filter(Customer.organization_id == org_id, Customer.customer_code == data.customer_code)
            .first()
        )
        if existing_code:
            raise DuplicateEntityException(f"Customer code '{data.customer_code}' already exists in this organization.")

        # Check duplicate email in org
        existing_email = (
            db.query(Customer)
            .filter(Customer.organization_id == org_id, Customer.email == data.email)
            .first()
        )
        if existing_email:
            raise DuplicateEntityException(f"Customer email '{data.email}' already exists in this organization.")

        customer = Customer(
            organization_id=org_id,
            customer_code=data.customer_code,
            company_name=data.company_name,
            contact_name=data.contact_name,
            email=data.email,
            phone=data.phone,
            billing_address=data.billing_address,
            tax_identifier=data.tax_identifier,
            status=data.status,
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)
        return customer

    @staticmethod
    def get_customer(db: Session, org_id: uuid.UUID, customer_id: uuid.UUID) -> Customer:
        customer = (
            db.query(Customer)
            .filter(Customer.organization_id == org_id, Customer.id == customer_id)
            .first()
        )
        if not customer:
            raise EntityNotFoundException("Customer", str(customer_id))
        return customer

    @staticmethod
    def update_customer(db: Session, org_id: uuid.UUID, customer_id: uuid.UUID, data: CustomerUpdate) -> Customer:
        customer = CustomerService.get_customer(db, org_id, customer_id)

        # Check uniqueness if updating customer_code
        if data.customer_code and data.customer_code != customer.customer_code:
            existing = (
                db.query(Customer)
                .filter(
                    Customer.organization_id == org_id,
                    Customer.customer_code == data.customer_code,
                    Customer.id != customer_id,
                )
                .first()
            )
            if existing:
                raise DuplicateEntityException(f"Customer code '{data.customer_code}' already in use.")
            customer.customer_code = data.customer_code

        # Check uniqueness if updating email
        if data.email and data.email != customer.email:
            existing = (
                db.query(Customer)
                .filter(
                    Customer.organization_id == org_id,
                    Customer.email == data.email,
                    Customer.id != customer_id,
                )
                .first()
            )
            if existing:
                raise DuplicateEntityException(f"Customer email '{data.email}' already in use.")
            customer.email = data.email

        update_dict = data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            if key not in ("customer_code", "email") and value is not None:
                setattr(customer, key, value)

        db.commit()
        db.refresh(customer)
        return customer

    @staticmethod
    def delete_or_deactivate_customer(db: Session, org_id: uuid.UUID, customer_id: uuid.UUID) -> Customer:
        customer = CustomerService.get_customer(db, org_id, customer_id)
        
        # Check if customer has active subscriptions
        from app.modules.subscriptions.models import Subscription
        active_subs = (
            db.query(Subscription)
            .filter(
                Subscription.customer_id == customer_id,
                Subscription.status.in_(["ACTIVE", "PAUSED"]),
            )
            .count()
        )
        if active_subs > 0:
            # Cannot hard delete a customer with active subscriptions; deactivate instead
            customer.status = "INACTIVE"
            db.commit()
            db.refresh(customer)
            return customer
        
        # Soft delete / deactivate
        customer.status = "INACTIVE"
        db.commit()
        db.refresh(customer)
        return customer

    @staticmethod
    def list_customers(
        db: Session,
        org_id: uuid.UUID,
        search: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> Tuple[List[Customer], int]:
        query = db.query(Customer).filter(Customer.organization_id == org_id)

        if status:
            query = query.filter(Customer.status == status.upper())

        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    Customer.customer_code.ilike(search_pattern),
                    Customer.company_name.ilike(search_pattern),
                    Customer.contact_name.ilike(search_pattern),
                    Customer.email.ilike(search_pattern),
                )
            )

        total = query.count()
        items = query.order_by(Customer.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
        return items, total

    @staticmethod
    def get_customer_invoices(db: Session, org_id: uuid.UUID, customer_id: uuid.UUID) -> List[Invoice]:
        CustomerService.get_customer(db, org_id, customer_id)
        return (
            db.query(Invoice)
            .filter(Invoice.organization_id == org_id, Invoice.customer_id == customer_id)
            .order_by(Invoice.issue_date.desc())
            .all()
        )
