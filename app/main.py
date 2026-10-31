from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import Base, engine
from app.core.auth import Organization, User
from app.modules.customers.models import Customer
from app.modules.products.models import Product, ProductVariant
from app.modules.plans.models import SubscriptionPlan, PlanPriceHistory
from app.modules.quotations.models import Quotation, QuotationItem
from app.modules.subscriptions.models import Subscription, SubscriptionItem, SubscriptionEvent
from app.modules.billing.models import (
    Invoice,
    InvoiceItem,
    BillingRun,
    BillingRunItem,
    TaxRule,
    Discount,
    DiscountRedemption,
    Payment,
    PaymentAllocation,
    PaymentRefund,
    ReconciliationRun,
    ReconciliationItem,
    Contract,
    ServiceCommitment,
    ServiceEvent,
    VerificationRun,
    VerificationResult,
    ServiceCredit,
    InvoiceAnomaly,
    AuditEvent,
)

from app.modules.customers.router import router as customer_router
from app.modules.products.router import product_router, variant_router
from app.modules.plans.router import router as plan_router
from app.modules.quotations.router import router as quotation_router
from app.modules.subscriptions.router import subscription_router, impact_router
from app.modules.billing.router import router as billing_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables if not exist (development convenience)
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="VERISUB Intelligent Subscription & Billing Verification Platform - Billing runs, invoices, taxes, discounts, payments, reconciliation, SLA contract verification, AI anomaly detection, and tamper-evident audit trail.",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API v1 Routers
api_v1_prefix = settings.API_V1_STR
app.include_router(customer_router, prefix=api_v1_prefix)
app.include_router(product_router, prefix=api_v1_prefix)
app.include_router(variant_router, prefix=api_v1_prefix)
app.include_router(plan_router, prefix=api_v1_prefix)
app.include_router(quotation_router, prefix=api_v1_prefix)
app.include_router(subscription_router, prefix=api_v1_prefix)
app.include_router(impact_router, prefix=api_v1_prefix)
app.include_router(billing_router, prefix=api_v1_prefix)


@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": "verisub-billing-verification",
        "version": settings.VERSION,
    }


@app.get("/", tags=["Root"])
def root():
    return {
        "message": "Welcome to VERISUB Intelligent Subscription & Billing Verification API",
        "docs": "/docs",
        "version": settings.VERSION,
    }
