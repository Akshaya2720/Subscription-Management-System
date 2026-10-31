"""User and staff member management router for VERISUB."""

from __future__ import annotations

from typing import Any, Optional
import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.app.core.permissions import PermissionEnum
from backend.app.db.session import get_db
from backend.app.dependencies.auth import require_permissions
from backend.app.models.membership import Membership
from backend.app.models.user import User
from backend.app.schemas.common import MessageResponse, PaginatedResponse
from backend.app.schemas.user import CreateStaffRequest, UpdateUserRequest, UserResponse
from backend.app.services import user_service

router = APIRouter(prefix="/api/v1/users", tags=["Users"])


@router.get(
    "/",
    response_model=PaginatedResponse[UserResponse],
    summary="List organization users and staff",
)
def list_users(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(default=None, description="Search by name or email"),
    is_active: Optional[bool] = Query(default=None, description="Filter by active status"),
    membership: Membership = Depends(
        require_permissions(PermissionEnum.MANAGE_STAFF)
    ),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """List users associated with the current organization.

    Supports search filtering and pagination.
    Requires MANAGE_STAFF permission.
    """
    return user_service.list_users(
        db=db,
        org_id=membership.organization_id,
        page=page,
        page_size=page_size,
        search=search,
        is_active=is_active,
    )


@router.post(
    "/staff",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new staff member",
)
def create_staff_user(
    payload: CreateStaffRequest,
    membership: Membership = Depends(
        require_permissions(PermissionEnum.MANAGE_STAFF)
    ),
    db: Session = Depends(get_db),
) -> User:
    """Create a new user with STAFF role in the current organization.

    Requires MANAGE_STAFF permission.
    """
    return user_service.create_staff_user(
        db=db,
        org_id=membership.organization_id,
        full_name=payload.full_name,
        email=payload.email,
        password=payload.password,
    )


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Retrieve user details by ID",
)
def get_user(
    user_id: uuid.UUID,
    membership: Membership = Depends(
        require_permissions(PermissionEnum.MANAGE_STAFF)
    ),
    db: Session = Depends(get_db),
) -> User:
    """Retrieve details for a specific user within the organization.

    Requires MANAGE_STAFF permission.
    """
    return user_service.get_user(
        db=db,
        user_id=user_id,
        org_id=membership.organization_id,
    )


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update user attributes",
)
def update_user(
    user_id: uuid.UUID,
    payload: UpdateUserRequest,
    membership: Membership = Depends(
        require_permissions(PermissionEnum.MANAGE_STAFF)
    ),
    db: Session = Depends(get_db),
) -> User:
    """Update user information (e.g., name, active status) in the organization.

    Requires MANAGE_STAFF permission.
    """
    return user_service.update_user(
        db=db,
        user_id=user_id,
        org_id=membership.organization_id,
        update_data=payload,
    )


@router.delete(
    "/{user_id}",
    response_model=MessageResponse,
    summary="Deactivate user membership",
)
def deactivate_user(
    user_id: uuid.UUID,
    membership: Membership = Depends(
        require_permissions(PermissionEnum.MANAGE_STAFF)
    ),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Deactivate a user's membership within the organization.

    Requires MANAGE_STAFF permission.
    """
    return user_service.deactivate_user(
        db=db,
        user_id=user_id,
        org_id=membership.organization_id,
    )
