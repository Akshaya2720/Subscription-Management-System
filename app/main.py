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
from app.modules.billing.models import Invoice, Payment

from app.modules.customers.router import router as customer_router
from app.modules.products.router import product_router, variant_router
from app.modules.plans.router import router as plan_router
from app.modules.quotations.router import router as quotation_router
from app.modules.subscriptions.router import subscription_router, impact_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables if not exist (development convenience)
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="VERISUB Subscription Engine Backend API - Managing complete software subscription lifecycle, quotation conversion, digital twin, and change impact preview.",
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

# Register Foundation, Auth, and RBAC Routers (Member 1)
from backend.app.routers import auth as auth_router_module
from backend.app.routers import organization as org_router_module
from backend.app.routers import users as users_router_module

app.include_router(auth_router_module.router)
app.include_router(org_router_module.router)
app.include_router(users_router_module.router)

# Register API v1 Routers (Member 2)
api_v1_prefix = settings.API_V1_STR
app.include_router(customer_router, prefix=api_v1_prefix)
app.include_router(product_router, prefix=api_v1_prefix)
app.include_router(variant_router, prefix=api_v1_prefix)
app.include_router(plan_router, prefix=api_v1_prefix)
app.include_router(quotation_router, prefix=api_v1_prefix)
app.include_router(subscription_router, prefix=api_v1_prefix)
app.include_router(impact_router, prefix=api_v1_prefix)


@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": "verisub-subscription-engine",
        "version": settings.VERSION,
    }


@app.get("/", tags=["Root"])
def root():
    return {
        "message": "Welcome to VERISUB Subscription Management System API",
        "docs": "/docs",
        "version": settings.VERSION,
    }
