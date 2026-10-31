"""Authentication, JWT verification, and Multi-Tenant Context Dependencies for VERISUB."""

import uuid
from typing import Optional, List, Callable
from fastapi import Depends, HTTPException, Header, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_token
from app.models.auth import Organization, User, UserRole

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_organization(
    x_organization_id: Optional[str] = Header(None, alias="X-Organization-Id"),
    db: Session = Depends(get_db),
) -> Organization:
    """
    Dependency to resolve the active organization.
    Multi-tenant isolation requires a valid organization.
    If X-Organization-Id is not supplied, auto-locates or creates the default organization for development ease.
    """
    if isinstance(x_organization_id, str):
        try:
            org_uuid = uuid.UUID(x_organization_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid X-Organization-Id header format. Must be a valid UUID.",
            )
        org = db.get(Organization, org_uuid)
        if not org or not org.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Organization not found or inactive.",
            )
        return org

    # If no header provided, find or seed default primary organization
    default_org = db.query(Organization).filter(Organization.slug == "default-org").first()
    if not default_org:
        default_org = Organization(
            id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
            name="Default Organization",
            slug="default-org",
            is_active=True,
        )
        db.add(default_org)
        db.commit()
        db.refresh(default_org)
    return default_org


def get_current_user(
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    bearer_auth: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db),
) -> User:
    """
    Dependency to retrieve the authenticated user within the organization.
    Supports JWT Bearer token, X-User-Id header, or seeded dev fallback.
    """
    # 1. Check Bearer JWT token
    if bearer_auth and bearer_auth.credentials:
        try:
            payload = decode_token(bearer_auth.credentials)
            if payload.get("type") != "access":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type: access token required",
                )
            user_id_str = payload.get("sub")
            if not user_id_str:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload: subject missing",
                )
            user = db.get(User, uuid.UUID(user_id_str))
            if not user or not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found or inactive",
                )
            return user
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )

    # 2. Check X-User-Id header
    if isinstance(x_user_id, str):
        try:
            user_uuid = uuid.UUID(x_user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid X-User-Id header format. Must be a valid UUID.",
            )
        user = db.get(User, user_uuid)
        if not user or user.organization_id != org.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User not found or does not belong to active organization.",
            )
        return user

    # 3. Default fallback user for dev/testing
    default_user = db.query(User).filter(User.organization_id == org.id, User.role == "ADMIN").first()
    if not default_user:
        default_user = User(
            id=uuid.UUID("00000000-0000-0000-0000-000000000002"),
            organization_id=org.id,
            email=f"admin@{org.slug}.local",
            password_hash="argon2id_dev_dummy_hash",
            full_name="Admin User",
            role="ADMIN",
            is_active=True,
        )
        db.add(default_user)
        db.commit()
        db.refresh(default_user)
    return default_user


def require_role(*allowed_roles: UserRole) -> Callable:
    """Dependency factory checking that the current user has one of the allowed roles."""
    def role_dependency(current_user: User = Depends(get_current_user)) -> User:
        user_role_str = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
        allowed_str_values = [r.value if hasattr(r, "value") else str(r) for r in allowed_roles]
        if user_role_str not in allowed_str_values:
            role_names = ", ".join(allowed_str_values)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Requires one of roles: [{role_names}]. Current role: {user_role_str}",
            )
        return current_user
    return role_dependency


def enforce_customer_scope(current_user: User, customer_id: uuid.UUID) -> None:
    """Enforce that CUSTOMER role can only access records matching their customer_id."""
    if current_user.role == UserRole.CUSTOMER:
        if not current_user.customer_id or current_user.customer_id != customer_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You do not have permission to access other customer records.",
            )
