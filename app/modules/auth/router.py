"""FastAPI routers for authentication, user management, and organization administration."""

from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_organization, get_current_user, require_role
from app.core.rate_limiter import rate_limit_auth
from app.models.auth import Organization, User, UserRole
from app.modules.auth.schemas import (
    RegisterRequest,
    LoginRequest,
    RefreshRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    StaffCreateRequest,
    UserResponse,
    OrganizationResponse,
    OrganizationUpdate,
    TokenResponse,
)
from app.modules.auth.service import AuthService
from app.modules.auth.repository import OrganizationRepository

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])
user_router = APIRouter(prefix="/users", tags=["Users"])
org_router = APIRouter(prefix="/organizations", tags=["Organizations"])


# ── Auth Endpoints ──────────────────────────────────────────────────────────

@auth_router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(rate_limit_auth)])
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new organization and root ADMIN account."""
    service = AuthService(db)
    return service.register(req)


@auth_router.post("/login", response_model=TokenResponse, dependencies=[Depends(rate_limit_auth)])
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate with email and password, returning JWT tokens."""
    service = AuthService(db)
    return service.login(req)


@auth_router.post("/refresh")
def refresh_token(req: RefreshRequest, db: Session = Depends(get_db)):
    """Exchange a valid refresh token for a newly signed access token."""
    service = AuthService(db)
    return service.refresh(req.refresh_token)


@auth_router.post("/logout")
def logout(req: RefreshRequest, db: Session = Depends(get_db)):
    """Revoke a refresh token."""
    service = AuthService(db)
    return service.logout(req.refresh_token)


@auth_router.post("/forgot-password", dependencies=[Depends(rate_limit_auth)])
def forgot_password(req: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Request a password reset link / token."""
    service = AuthService(db)
    return service.forgot_password(req.email)


@auth_router.post("/reset-password", dependencies=[Depends(rate_limit_auth)])
def reset_password(req: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Reset password using a verified reset token."""
    service = AuthService(db)
    return service.reset_password(req.token, req.new_password)


# ── User Endpoints ──────────────────────────────────────────────────────────

@user_router.get("/", response_model=List[UserResponse])
def list_users(
    org: Organization = Depends(get_current_organization),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    """List all users within the current organization. ADMIN only."""
    service = AuthService(db)
    return service.list_users(org.id)


@user_router.post("/staff", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_staff(
    req: StaffCreateRequest,
    org: Organization = Depends(get_current_organization),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    """Create a new staff member within the current organization. ADMIN only."""
    service = AuthService(db)
    return service.create_staff(org.id, req)


# ── Organization Endpoints ──────────────────────────────────────────────────

@org_router.get("/current", response_model=OrganizationResponse)
def get_current_org(
    org: Organization = Depends(get_current_organization),
    current_user: User = Depends(get_current_user),
):
    """Retrieve details for the active organization."""
    return OrganizationResponse.model_validate(org)


@org_router.patch("/current", response_model=OrganizationResponse)
def update_current_org(
    req: OrganizationUpdate,
    org: Organization = Depends(get_current_organization),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    """Update active organization settings. ADMIN only."""
    repo = OrganizationRepository(db)
    updated = repo.update(org, name=req.name, is_active=req.is_active)
    db.commit()
    db.refresh(updated)
    return OrganizationResponse.model_validate(updated)
