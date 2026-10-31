"""Main FastAPI application entrypoint for VERISUB."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.core.config import settings
from backend.app.routers import auth, customers, organization, users

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Intelligent Subscription and Billing Verification Platform",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth.router)
app.include_router(organization.router)
app.include_router(users.router)
app.include_router(customers.router)


@app.get("/", tags=["Health"])
def health_check():
    """Root health check endpoint."""
    return {"status": "healthy", "app": settings.APP_NAME, "version": settings.APP_VERSION}


@app.get("/api/v1/health", tags=["Health"])
def api_health():
    """API v1 health status endpoint."""
    return {"status": "healthy"}
