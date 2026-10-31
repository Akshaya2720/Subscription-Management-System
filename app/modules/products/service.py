import uuid
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session

from app.modules.products.models import Product, ProductVariant
from app.modules.products.repository import ProductRepository, VariantRepository
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
        repo = ProductRepository(db)
        if repo.get_by_name(org_id, data.name):
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
        repo = ProductRepository(db)
        product = repo.get_by_id(org_id, product_id)
        if not product:
            raise EntityNotFoundException("Product", str(product_id))
        return product

    @staticmethod
    def update_product(db: Session, org_id: uuid.UUID, product_id: uuid.UUID, data: ProductUpdate) -> Product:
        repo = ProductRepository(db)
        product = ProductService.get_product(db, org_id, product_id)

        if data.name and data.name != product.name:
            if repo.get_by_name(org_id, data.name, exclude_id=product_id):
                raise DuplicateEntityException(f"Product name '{data.name}' already in use.")
            product.name = data.name

        update_dict = data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            if key != "name" and value is not None:
                setattr(product, key, value)

        return repo.save(product)

    @staticmethod
    def delete_or_deactivate_product(db: Session, org_id: uuid.UUID, product_id: uuid.UUID) -> Product:
        repo = ProductRepository(db)
        product = ProductService.get_product(db, org_id, product_id)
        product.status = "ARCHIVED"
        return repo.save(product)

    @staticmethod
    def list_products(
        db: Session,
        org_id: uuid.UUID,
        search: Optional[str] = None,
        product_type: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
        skip: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> Tuple[List[Product], int]:
        repo = ProductRepository(db)
        actual_skip = skip if skip is not None else (page - 1) * per_page
        actual_limit = limit if limit is not None else per_page
        return repo.list(
            org_id,
            search=search,
            product_type=product_type,
            status=status,
            skip=actual_skip,
            limit=actual_limit,
        )

    # Variant operations
    @staticmethod
    def create_variant(db: Session, org_id: uuid.UUID, product_id: uuid.UUID, data: VariantCreate) -> ProductVariant:
        ProductService.get_product(db, org_id, product_id)
        v_repo = VariantRepository(db)

        variant = ProductVariant(
            product_id=product_id,
            variant_name=data.variant_name,
            description=data.description,
            additional_price=data.additional_price,
            status=data.status,
        )
        return v_repo.save(variant)

    @staticmethod
    def get_variant(db: Session, org_id: uuid.UUID, product_id: uuid.UUID, variant_id: uuid.UUID) -> ProductVariant:
        ProductService.get_product(db, org_id, product_id)
        v_repo = VariantRepository(db)
        variant = v_repo.get_by_id(product_id, variant_id)
        if not variant:
            raise EntityNotFoundException("ProductVariant", str(variant_id))
        return variant

    @staticmethod
    def update_variant(
        db: Session, org_id: uuid.UUID, variant_id: uuid.UUID, data: VariantUpdate
    ) -> ProductVariant:
        v_repo = VariantRepository(db)
        variant = v_repo.get_by_id_direct(variant_id)
        if not variant:
            raise EntityNotFoundException("ProductVariant", str(variant_id))

        update_dict = data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            if value is not None:
                setattr(variant, key, value)

        return v_repo.save(variant)

    @staticmethod
    def list_variants(db: Session, org_id: uuid.UUID, product_id: uuid.UUID) -> List[ProductVariant]:
        ProductService.get_product(db, org_id, product_id)
        v_repo = VariantRepository(db)
        return v_repo.list_by_product(product_id)

    @staticmethod
    def delete_variant(db: Session, org_id: uuid.UUID, variant_id: uuid.UUID) -> ProductVariant:
        v_repo = VariantRepository(db)
        variant = v_repo.get_by_id_direct(variant_id)
        if not variant:
            raise EntityNotFoundException("ProductVariant", str(variant_id))
        variant.status = "INACTIVE"
        return v_repo.save(variant)
