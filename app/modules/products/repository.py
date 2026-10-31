"""Repository layer for products and product variants."""

import uuid
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.modules.products.models import Product, ProductVariant


class ProductRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, org_id: uuid.UUID, product_id: uuid.UUID) -> Optional[Product]:
        return (
            self.db.query(Product)
            .filter(Product.organization_id == org_id, Product.id == product_id)
            .first()
        )

    def get_by_name(self, org_id: uuid.UUID, name: str, exclude_id: Optional[uuid.UUID] = None) -> Optional[Product]:
        q = self.db.query(Product).filter(
            Product.organization_id == org_id,
            Product.name == name,
        )
        if exclude_id:
            q = q.filter(Product.id != exclude_id)
        return q.first()

    def list(
        self,
        org_id: uuid.UUID,
        search: Optional[str] = None,
        product_type: Optional[str] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[Product], int]:
        query = self.db.query(Product).filter(Product.organization_id == org_id)
        if search:
            query = query.filter(
                or_(
                    Product.name.ilike(f"%{search}%"),
                    Product.description.ilike(f"%{search}%"),
                )
            )
        if product_type:
            query = query.filter(Product.product_type == product_type)
        if status:
            query = query.filter(Product.status == status)

        total = query.count()
        products = query.order_by(Product.name.asc()).offset(skip).limit(limit).all()
        return products, total

    def save(self, product: Product) -> Product:
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        return product


class VariantRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id_direct(self, variant_id: uuid.UUID) -> Optional[ProductVariant]:
        return self.db.query(ProductVariant).filter(ProductVariant.id == variant_id).first()

    def get_by_id(self, product_id: uuid.UUID, variant_id: uuid.UUID) -> Optional[ProductVariant]:
        return (
            self.db.query(ProductVariant)
            .filter(ProductVariant.product_id == product_id, ProductVariant.id == variant_id)
            .first()
        )

    def list_by_product(self, product_id: uuid.UUID) -> List[ProductVariant]:
        return self.db.query(ProductVariant).filter(ProductVariant.product_id == product_id).all()

    def save(self, variant: ProductVariant) -> ProductVariant:
        self.db.add(variant)
        self.db.commit()
        self.db.refresh(variant)
        return variant

    def delete(self, variant: ProductVariant) -> None:
        self.db.delete(variant)
        self.db.commit()
