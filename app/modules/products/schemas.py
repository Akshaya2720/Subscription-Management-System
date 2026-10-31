import uuid
from decimal import Decimal
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict, field_validator


class VariantBase(BaseModel):
    variant_name: str = Field(..., max_length=255, description="Name of the variant, e.g. Premium Support")
    description: Optional[str] = Field(None, description="Detailed description")
    additional_price: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"), description="Additional price over base product")
    status: str = Field("ACTIVE", description="Status: ACTIVE, INACTIVE")

    @field_validator("additional_price", mode="before")
    @classmethod
    def validate_decimal(cls, v):
        if v is not None:
            return Decimal(str(v)).quantize(Decimal("0.01"))
        return Decimal("0.00")


class VariantCreate(VariantBase):
    pass


class VariantUpdate(BaseModel):
    variant_name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    additional_price: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    status: Optional[str] = None

    @field_validator("additional_price", mode="before")
    @classmethod
    def validate_decimal(cls, v):
        if v is not None:
            return Decimal(str(v)).quantize(Decimal("0.01"))
        return None


class VariantResponse(VariantBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    product_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class ProductBase(BaseModel):
    name: str = Field(..., max_length=255, description="Product name")
    product_type: str = Field("SAAS", description="Product type, e.g. SAAS, SERVICE, GOODS, LICENSE")
    description: Optional[str] = Field(None, description="Product description")
    sales_price: Decimal = Field(..., ge=Decimal("0.00"), description="Base sales price")
    cost_price: Optional[Decimal] = Field(None, ge=Decimal("0.00"), description="Base cost price")
    notes: Optional[str] = Field(None, description="Internal notes")
    status: str = Field("ACTIVE", description="Status: ACTIVE, INACTIVE, ARCHIVED")

    @field_validator("sales_price", "cost_price", mode="before")
    @classmethod
    def validate_decimals(cls, v):
        if v is not None:
            return Decimal(str(v)).quantize(Decimal("0.01"))
        return None


class ProductCreate(ProductBase):
    variants: Optional[List[VariantCreate]] = None


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    product_type: Optional[str] = None
    description: Optional[str] = None
    sales_price: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    cost_price: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    notes: Optional[str] = None
    status: Optional[str] = None

    @field_validator("sales_price", "cost_price", mode="before")
    @classmethod
    def validate_decimals(cls, v):
        if v is not None:
            return Decimal(str(v)).quantize(Decimal("0.01"))
        return None


class ProductResponse(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    variants: List[VariantResponse] = []


class ProductPaginatedResponse(BaseModel):
    items: List[ProductResponse]
    total: int
    page: int
    per_page: int
    pages: int
