"""FastAPI dependencies for authentication and authorization."""

from typing import Optional
import uuid

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session, joinedload

from backend.app.core.permissions import PermissionEnum
from backend.app.core.security import decode_token
from backend.app.db.session import get_db
from backend.app.models import (
    Membership,
    MembershipRole,
    Permission,
    Role,
    RolePermission,
    User,
)

security_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Validate access token from bearer authorization header and return current User.

    Raises:
        HTTPException 401: If token is missing, invalid, expired, non-access, or user inactive.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not credentials or not credentials.credentials:
        raise credentials_exception

    try:
        payload = decode_token(credentials.credentials)
        if not isinstance(payload, dict):
            raise credentials_exception

        token_type = payload.get("type")
        if token_type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user_id_str = payload.get("sub")
        if not user_id_str:
            raise credentials_exception

        user_id = uuid.UUID(str(user_id_str))
    except HTTPException:
        raise
    except Exception as exc:
        raise credentials_exception from exc

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def get_organization_id(
    x_organization_id: uuid.UUID = Header(
        ...,
        alias="X-Organization-ID",
        description="Tenant organization ID header",
    ),
) -> uuid.UUID:
    """Extract required active organization UUID from X-Organization-ID request header."""
    return x_organization_id


def get_optional_organization_id(
    x_organization_id: Optional[uuid.UUID] = Header(
        default=None,
        alias="X-Organization-ID",
        description="Optional tenant organization ID header",
    ),
) -> Optional[uuid.UUID]:
    """Extract optional organization UUID from X-Organization-ID request header."""
    return x_organization_id


def get_current_membership(
    current_user: User = Depends(get_current_user),
    organization_id: uuid.UUID = Depends(get_organization_id),
    db: Session = Depends(get_db),
) -> Membership:
    """Verify and retrieve current user's active membership in the specified organization."""
    membership = (
        db.query(Membership)
        .options(
            joinedload(Membership.organization),
            joinedload(Membership.membership_roles).joinedload(MembershipRole.role),
        )
        .filter(
            Membership.user_id == current_user.id,
            Membership.organization_id == organization_id,
            Membership.status == "active",
        )
        .first()
    )

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: No active membership found in this organization",
        )

    return membership


def get_current_active_membership(
    organization_id: Optional[uuid.UUID] = Depends(get_optional_organization_id),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Membership:
    """Resolve active membership from header or infer single membership."""
    if organization_id is not None:
        membership = (
            db.query(Membership)
            .options(
                joinedload(Membership.organization),
                joinedload(Membership.membership_roles).joinedload(MembershipRole.role),
            )
            .filter(
                Membership.user_id == current_user.id,
                Membership.organization_id == organization_id,
                Membership.status == "active",
            )
            .first()
        )
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: No active membership found in this organization",
            )
        return membership

    memberships = (
        db.query(Membership)
        .options(
            joinedload(Membership.organization),
            joinedload(Membership.membership_roles).joinedload(MembershipRole.role),
        )
        .filter(
            Membership.user_id == current_user.id,
            Membership.status == "active",
        )
        .all()
    )

    if not memberships:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User has no active organization memberships",
        )

    if len(memberships) > 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Multiple active organizations found. Please specify organization context using the X-Organization-ID header",
        )

    return memberships[0]


def get_user_permissions(
    membership: Membership = Depends(get_current_membership),
    db: Session = Depends(get_db),
) -> set[str]:
    """Retrieve all permission names granted across all roles for current membership."""
    role_ids = [mr.role_id for mr in membership.membership_roles]
    if not role_ids:
        return set()

    permissions = (
        db.query(Permission.permission_name)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .filter(RolePermission.role_id.in_(role_ids))
        .all()
    )
    return {p[0] for p in permissions}


def require_permissions(*required_permissions: str | PermissionEnum):
    """Dependency factory checking user has all specified permissions."""

    async def _check(
        membership: Membership = Depends(get_current_membership),
        db: Session = Depends(get_db),
    ) -> Membership:
        perm_names = [
            p.value if hasattr(p, "value") else str(p)
            for p in required_permissions
        ]

        role_ids = [mr.role_id for mr in membership.membership_roles]
        if not role_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No roles assigned",
            )

        permissions = (
            db.query(Permission.permission_name)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .filter(RolePermission.role_id.in_(role_ids))
            .all()
        )

        user_permissions = {p[0] for p in permissions}

        missing = set(perm_names) - user_permissions
        if missing:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permissions: {', '.join(sorted(missing))}",
            )

        return membership

    return _check


def require_role(*required_roles: str):
    """Dependency factory checking user has at least one of the specified roles."""

    async def _check(
        membership: Membership = Depends(get_current_membership),
    ) -> Membership:
        user_role_names = {
            mr.role.name
            for mr in membership.membership_roles
            if mr.role and mr.role.name
        }
        allowed = set(required_roles)
        if not (user_role_names & allowed):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role required: one of [{', '.join(sorted(allowed))}]. User has [{', '.join(sorted(user_role_names))}]",
            )

        return membership

    return _check
