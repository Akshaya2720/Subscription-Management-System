import uuid
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session

from app.modules.customers.models import Customer, CustomerStatus
from app.modules.customers.schemas import CustomerCreate, CustomerUpdate
from app.modules.customers.repository import CustomerRepository
from app.core.exceptions import EntityNotFoundException, DuplicateEntityException, BusinessRuleValidationException
from app.modules.billing.models import Invoice


class CustomerService:
    @staticmethod
    def create_customer(db: Session, org_id: uuid.UUID, data: CustomerCreate) -> Customer:
        repo = CustomerRepository(db)
        if repo.get_by_code(org_id, data.customer_code):
            raise DuplicateEntityException(f"Customer code '{data.customer_code}' already exists in this organization.")

        if repo.get_by_email(org_id, data.email):
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
        return repo.save(customer)

    @staticmethod
    def get_customer(db: Session, org_id: uuid.UUID, customer_id: uuid.UUID) -> Customer:
        repo = CustomerRepository(db)
        customer = repo.get_by_id(org_id, customer_id)
        if not customer:
            raise EntityNotFoundException("Customer", str(customer_id))
        return customer

    @staticmethod
    def update_customer(db: Session, org_id: uuid.UUID, customer_id: uuid.UUID, data: CustomerUpdate) -> Customer:
        repo = CustomerRepository(db)
        customer = CustomerService.get_customer(db, org_id, customer_id)

        if data.customer_code and data.customer_code != customer.customer_code:
            if repo.get_by_code(org_id, data.customer_code, exclude_id=customer_id):
                raise DuplicateEntityException(f"Customer code '{data.customer_code}' already in use.")
            customer.customer_code = data.customer_code

        if data.email and data.email != customer.email:
            if repo.get_by_email(org_id, data.email, exclude_id=customer_id):
                raise DuplicateEntityException(f"Customer email '{data.email}' already in use.")
            customer.email = data.email

        update_dict = data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            if key not in ("customer_code", "email") and value is not None:
                setattr(customer, key, value)

        return repo.save(customer)

    @staticmethod
    def list_customers(
        db: Session,
        org_id: uuid.UUID,
        search: Optional[str] = None,
        status: Optional[CustomerStatus] = None,
        page: int = 1,
        per_page: int = 20,
        skip: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> Tuple[List[Customer], int]:
        repo = CustomerRepository(db)
        actual_skip = skip if skip is not None else (page - 1) * per_page
        actual_limit = limit if limit is not None else per_page
        return repo.list(org_id, search=search, status=status, skip=actual_skip, limit=actual_limit)

    @staticmethod
    def delete_or_deactivate_customer(db: Session, org_id: uuid.UUID, customer_id: uuid.UUID) -> Customer:
        repo = CustomerRepository(db)
        customer = CustomerService.get_customer(db, org_id, customer_id)
        customer.status = CustomerStatus.INACTIVE
        return repo.save(customer)

    @staticmethod
    def delete_customer(db: Session, org_id: uuid.UUID, customer_id: uuid.UUID) -> None:
        repo = CustomerRepository(db)
        customer = CustomerService.get_customer(db, org_id, customer_id)
        if customer.subscriptions and len(customer.subscriptions) > 0:
            raise BusinessRuleValidationException("Cannot delete customer with active or associated subscriptions.")
        repo.delete(customer)

    @staticmethod
    def get_customer_invoices(db: Session, org_id: uuid.UUID, customer_id: uuid.UUID):
        CustomerService.get_customer(db, org_id, customer_id)
        return (
            db.query(Invoice)
            .filter(Invoice.organization_id == org_id, Invoice.customer_id == customer_id)
            .order_by(Invoice.issue_date.desc())
            .all()
        )
