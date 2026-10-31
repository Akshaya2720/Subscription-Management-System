from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import Base, engine
from app.models import (
    Organization,
    User,
    Customer,
    Product,
    ProductVariant,
    SubscriptionPlan,
    PlanPriceHistory,
    Quotation,
    QuotationItem,
    Subscription,
    SubscriptionItem,
    SubscriptionEvent,
    Invoice,
    Payment,
    TaxRule,
    Discount,
    VerificationContract,
    AuditLog,
)

# API Routers
from app.modules.auth.router import auth_router, user_router, org_router
from app.modules.customers.router import router as customer_router
from app.modules.products.router import product_router, variant_router
from app.modules.plans.router import router as plan_router
from app.modules.quotations.router import router as quotation_router
from app.modules.subscriptions.router import subscription_router, impact_router
from app.modules.billing.router import tax_router, discount_router, invoice_router
from app.modules.verification.router import verification_router, audit_router
from app.modules.dashboard.router import dashboard_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure all tables created in development
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="VERISUB Intelligent Subscription & Billing Verification Platform API - Managing complete lifecycle, quotations, idempotent billing, simulated payments, SLA verification, and SHA-256 tamper-evident audit ledger.",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://0.0.0.0:3000",
        "http://0.0.0.0:5173",
    ],
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Foundation, Auth, and RBAC Routers (Member 1)
from backend.app.routers import auth as auth_router_module
from backend.app.routers import organization as org_router_module
from backend.app.routers import users as users_router_module

app.include_router(auth_router_module.router)
app.include_router(org_router_module.router)
app.include_router(users_router_module.router)

# Register API v1 Routers (Member 2)
api_v1_prefix = settings.API_V1_STR
app.include_router(auth_router, prefix=api_v1_prefix)
app.include_router(user_router, prefix=api_v1_prefix)
app.include_router(org_router, prefix=api_v1_prefix)
app.include_router(customer_router, prefix=api_v1_prefix)
app.include_router(product_router, prefix=api_v1_prefix)
app.include_router(variant_router, prefix=api_v1_prefix)
app.include_router(plan_router, prefix=api_v1_prefix)
app.include_router(quotation_router, prefix=api_v1_prefix)
app.include_router(subscription_router, prefix=api_v1_prefix)
app.include_router(impact_router, prefix=api_v1_prefix)
app.include_router(tax_router, prefix=api_v1_prefix)
app.include_router(discount_router, prefix=api_v1_prefix)
app.include_router(invoice_router, prefix=api_v1_prefix)
app.include_router(verification_router, prefix=api_v1_prefix)
app.include_router(audit_router, prefix=api_v1_prefix)
app.include_router(dashboard_router, prefix=api_v1_prefix)


@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": "verisub-platform-engine",
        "version": settings.VERSION,
    }


@app.get("/", tags=["Root"])
def root():
    return {
        "message": "Welcome to VERISUB Intelligent Subscription & Billing Verification Platform API",
        "docs": "/docs",
        "version": settings.VERSION,
    }
