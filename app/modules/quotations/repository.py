"""Repository layer for quotations and quotation templates."""

import uuid
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session

from app.modules.quotations.models import Quotation, QuotationItem, QuotationTemplate, QuotationTemplateItem


class QuotationRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, org_id: uuid.UUID, quotation_id: uuid.UUID) -> Optional[Quotation]:
        return (
            self.db.query(Quotation)
            .filter(Quotation.organization_id == org_id, Quotation.id == quotation_id)
            .first()
        )

    def get_by_number(self, org_id: uuid.UUID, quotation_number: str) -> Optional[Quotation]:
        return (
            self.db.query(Quotation)
            .filter(Quotation.organization_id == org_id, Quotation.quotation_number == quotation_number)
            .first()
        )

    def list(
        self,
        org_id: uuid.UUID,
        customer_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> Tuple[List[Quotation], int]:
        query = self.db.query(Quotation).filter(Quotation.organization_id == org_id)
        if customer_id:
            query = query.filter(Quotation.customer_id == customer_id)
        if status:
            query = query.filter(Quotation.status == status.upper())

        total = query.count()
        items = query.order_by(Quotation.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
        return items, total

    def save(self, quotation: Quotation) -> Quotation:
        self.db.add(quotation)
        self.db.commit()
        self.db.refresh(quotation)
        return quotation

    # Templates
    def get_template(self, org_id: uuid.UUID, template_id: uuid.UUID) -> Optional[QuotationTemplate]:
        return (
            self.db.query(QuotationTemplate)
            .filter(QuotationTemplate.organization_id == org_id, QuotationTemplate.id == template_id)
            .first()
        )

    def list_templates(self, org_id: uuid.UUID) -> List[QuotationTemplate]:
        return (
            self.db.query(QuotationTemplate)
            .filter(QuotationTemplate.organization_id == org_id, QuotationTemplate.is_active == True)
            .order_by(QuotationTemplate.name.asc())
            .all()
        )

    def save_template(self, template: QuotationTemplate) -> QuotationTemplate:
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        return template
