import uuid
import math
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_organization, Organization
from app.modules.products.schemas import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductPaginatedResponse,
    VariantCreate,
    VariantUpdate,
    VariantResponse,
)
from app.modules.products.service import ProductService

product_router = APIRouter(prefix="/products", tags=["Products"])
variant_router = APIRouter(tags=["Variants"])


# --- Products Endpoints ---

@product_router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    payload: ProductCreate,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """Create a new product with optional initial variants."""
    return ProductService.create_product(db, org.id, payload)


@product_router.get("", response_model=ProductPaginatedResponse)
def list_products(
    search: Optional[str] = Query(None, description="Search product name or description"),
    status: Optional[str] = Query(None, description="Filter by status (ACTIVE, INACTIVE, ARCHIVED)"),
    product_type: Optional[str] = Query(None, description="Filter by product type"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """Search and filter products with pagination."""
    items, total = ProductService.list_products(
        db, org.id, search=search, status=status, product_type=product_type, page=page, per_page=per_page
    )
    pages = math.ceil(total / per_page) if per_page else 1
    return ProductPaginatedResponse(items=items, total=total, page=page, per_page=per_page, pages=pages)


@product_router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: uuid.UUID,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """Get product details by ID."""
    return ProductService.get_product(db, org.id, product_id)


@product_router.patch("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: uuid.UUID,
    payload: ProductUpdate,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """Update product details."""
    return ProductService.update_product(db, org.id, product_id, payload)


@product_router.delete("/{product_id}", response_model=ProductResponse)
def delete_product(
    product_id: uuid.UUID,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """Deactivate or archive a product."""
    return ProductService.delete_or_deactivate_product(db, org.id, product_id)


# --- Variant Endpoints under Product ---

@product_router.post("/{product_id}/variants", response_model=VariantResponse, status_code=status.HTTP_201_CREATED)
def create_variant_for_product(
    product_id: uuid.UUID,
    payload: VariantCreate,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """Create a new variant under the specified product."""
    return ProductService.create_variant(db, org.id, product_id, payload)


@product_router.get("/{product_id}/variants", response_model=List[VariantResponse])
def list_variants_for_product(
    product_id: uuid.UUID,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """List all variants for a given product."""
    return ProductService.list_variants(db, org.id, product_id)


# --- Direct Variant Endpoints ---

@variant_router.patch("/variants/{variant_id}", response_model=VariantResponse)
def update_variant(
    variant_id: uuid.UUID,
    payload: VariantUpdate,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """Update variant details and additional price."""
    return ProductService.update_variant(db, org.id, variant_id, payload)


@variant_router.delete("/variants/{variant_id}", response_model=VariantResponse)
def delete_variant(
    variant_id: uuid.UUID,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_organization),
):
    """Deactivate a variant."""
    return ProductService.delete_variant(db, org.id, variant_id)
