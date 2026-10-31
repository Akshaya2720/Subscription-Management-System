import uuid
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.modules.products.models import Product, ProductVariant
from app.modules.products.schemas import (
    ProductCreate,
    ProductUpdate,
    VariantCreate,
    VariantUpdate,
)
from app.core.exceptions import EntityNotFoundException, DuplicateEntityException


class ProductService:
    @staticmethod
    def create_product(db: Session, org_id: uuid.UUID, data: ProductCreate) -> Product:
        existing = (
            db.query(Product)
            .filter(Product.organization_id == org_id, Product.name == data.name)
            .first()
        )
        if existing:
            raise DuplicateEntityException(f"Product with name '{data.name}' already exists.")

        product = Product(
            organization_id=org_id,
            name=data.name,
            product_type=data.product_type,
            description=data.description,
            sales_price=data.sales_price,
            cost_price=data.cost_price,
            notes=data.notes,
            status=data.status,
        )
        db.add(product)
        db.flush()

        if data.variants:
            for v_data in data.variants:
                variant = ProductVariant(
                    product_id=product.id,
                    variant_name=v_data.variant_name,
                    description=v_data.description,
                    additional_price=v_data.additional_price,
                    status=v_data.status,
                )
                db.add(variant)

        db.commit()
        db.refresh(product)
        return product

    @staticmethod
    def get_product(db: Session, org_id: uuid.UUID, product_id: uuid.UUID) -> Product:
        product = (
            db.query(Product)
            .filter(Product.organization_id == org_id, Product.id == product_id)
            .first()
        )
        if not product:
            raise EntityNotFoundException("Product", str(product_id))
        return product

    @staticmethod
    def update_product(db: Session, org_id: uuid.UUID, product_id: uuid.UUID, data: ProductUpdate) -> Product:
        product = ProductService.get_product(db, org_id, product_id)

        if data.name and data.name != product.name:
            existing = (
                db.query(Product)
                .filter(
                    Product.organization_id == org_id,
                    Product.name == data.name,
                    Product.id != product_id,
                )
                .first()
            )
            if existing:
                raise DuplicateEntityException(f"Product name '{data.name}' already in use.")
            product.name = data.name

        update_dict = data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            if key != "name" and value is not None:
                setattr(product, key, value)

        db.commit()
        db.refresh(product)
        return product

    @staticmethod
    def delete_or_deactivate_product(db: Session, org_id: uuid.UUID, product_id: uuid.UUID) -> Product:
        product = ProductService.get_product(db, org_id, product_id)
        product.status = "ARCHIVED"
        db.commit()
        db.refresh(product)
        return product

    @staticmethod
    def list_products(
        db: Session,
        org_id: uuid.UUID,
        search: Optional[str] = None,
        status: Optional[str] = None,
        product_type: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> Tuple[List[Product], int]:
        query = db.query(Product).filter(Product.organization_id == org_id)

        if status:
            query = query.filter(Product.status == status.upper())

        if product_type:
            query = query.filter(Product.product_type == product_type.upper())

        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    Product.name.ilike(search_pattern),
                    Product.description.ilike(search_pattern),
                )
            )

        total = query.count()
        items = query.order_by(Product.name.asc()).offset((page - 1) * per_page).limit(per_page).all()
        return items, total

    # Variant operations
    @staticmethod
    def create_variant(db: Session, org_id: uuid.UUID, product_id: uuid.UUID, data: VariantCreate) -> ProductVariant:
        product = ProductService.get_product(db, org_id, product_id)
        existing = (
            db.query(ProductVariant)
            .filter(
                ProductVariant.product_id == product.id,
                ProductVariant.variant_name == data.variant_name,
            )
            .first()
        )
        if existing:
            raise DuplicateEntityException(f"Variant '{data.variant_name}' already exists for this product.")

        variant = ProductVariant(
            product_id=product.id,
            variant_name=data.variant_name,
            description=data.description,
            additional_price=data.additional_price,
            status=data.status,
        )
        db.add(variant)
        db.commit()
        db.refresh(variant)
        return variant

    @staticmethod
    def list_variants(db: Session, org_id: uuid.UUID, product_id: uuid.UUID) -> List[ProductVariant]:
        product = ProductService.get_product(db, org_id, product_id)
        return db.query(ProductVariant).filter(ProductVariant.product_id == product.id).all()

    @staticmethod
    def get_variant(db: Session, org_id: uuid.UUID, variant_id: uuid.UUID) -> ProductVariant:
        variant = (
            db.query(ProductVariant)
            .join(Product, ProductVariant.product_id == Product.id)
            .filter(Product.organization_id == org_id, ProductVariant.id == variant_id)
            .first()
        )
        if not variant:
            raise EntityNotFoundException("ProductVariant", str(variant_id))
        return variant

    @staticmethod
    def update_variant(db: Session, org_id: uuid.UUID, variant_id: uuid.UUID, data: VariantUpdate) -> ProductVariant:
        variant = ProductService.get_variant(db, org_id, variant_id)

        if data.variant_name and data.variant_name != variant.variant_name:
            existing = (
                db.query(ProductVariant)
                .filter(
                    ProductVariant.product_id == variant.product_id,
                    ProductVariant.variant_name == data.variant_name,
                    ProductVariant.id != variant_id,
                )
                .first()
            )
            if existing:
                raise DuplicateEntityException(f"Variant name '{data.variant_name}' already exists.")
            variant.variant_name = data.variant_name

        update_dict = data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            if key != "variant_name" and value is not None:
                setattr(variant, key, value)

        db.commit()
        db.refresh(variant)
        return variant

    @staticmethod
    def delete_variant(db: Session, org_id: uuid.UUID, variant_id: uuid.UUID) -> ProductVariant:
        variant = ProductService.get_variant(db, org_id, variant_id)
        variant.status = "INACTIVE"
        db.commit()
        db.refresh(variant)
        return variant
