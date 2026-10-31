"""User and staff member management service for VERISUB."""

from __future__ import annotations

import math
from typing import Any, Optional, Union
import uuid

from fastapi import HTTPException, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload, selectinload

from backend.app.core.permissions import RoleEnum
from backend.app.core.security import hash_password, validate_password
from backend.app.models.membership import Membership
from backend.app.models.organization import Organization
from backend.app.models.role import MembershipRole, Role
from backend.app.models.user import User
from backend.app.services.auth_service import _ensure_roles_and_permissions


def list_users(
    db: Session,
    org_id: uuid.UUID,
    page: int = 1,
    page_size: int = 20,
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
) -> dict[str, Any]:
    """List users belonging to an organization with search, filtering, and pagination."""
    # Ensure safe pagination parameters
    page = max(1, page)
    page_size = max(1, min(page_size, 100))

    query = (
        db.query(User, Membership)
        .join(Membership, Membership.user_id == User.id)
        .filter(Membership.organization_id == org_id)
        .options(
            selectinload(Membership.membership_roles).joinedload(MembershipRole.role)
        )
    )

    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                User.full_name.ilike(term),
                User.email.ilike(term),
            )
        )

    if is_active is not None:
        query = query.filter(User.is_active == is_active)

    total = query.count()
    offset = (page - 1) * page_size
    records = (
        query.order_by(User.created_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )

    items = []
    for user_obj, membership_obj in records:
        roles = [
            mr.role.name
            for mr in membership_obj.membership_roles
            if mr.role and mr.role.name
        ]
        items.append({
            "id": user_obj.id,
            "full_name": user_obj.full_name,
            "email": user_obj.email,
            "is_active": user_obj.is_active,
            "email_verified": user_obj.email_verified,
            "created_at": user_obj.created_at,
            "updated_at": user_obj.updated_at,
            "roles": roles,
        })

    total_pages = math.ceil(total / page_size) if page_size > 0 else 0

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


def create_staff_user(
    db: Session,
    org_id: uuid.UUID,
    full_name: str,
    email: str,
    password: str,
) -> User:
    """Create a new staff user and associate them with the specified organization."""
    # 1. Validate password rules
    is_valid, error_msg = validate_password(password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg,
        )

    norm_email = email.strip().lower()

    # 2. Check if email is already in use
    existing_user = db.query(User).filter(User.email == norm_email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email address already exists.",
        )

    # 3. Verify organization exists
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization with ID '{org_id}' not found.",
        )

    # 4. Create User entity
    user = User(
        full_name=full_name.strip(),
        email=norm_email,
        password_hash=hash_password(password),
        is_active=True,
        email_verified=False,
    )
    db.add(user)
    db.flush()

    # 5. Create Membership entity
    membership = Membership(
        organization_id=org_id,
        user_id=user.id,
        status="active",
    )
    db.add(membership)
    db.flush()

    # 6. Ensure standard roles and assign STAFF role
    roles_map = _ensure_roles_and_permissions(db)
    staff_role = roles_map.get(RoleEnum.STAFF.value)
    if not staff_role:
        staff_role = db.query(Role).filter(Role.name == RoleEnum.STAFF.value).first()

    if not staff_role:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="STAFF role not configured.",
        )

    membership_role = MembershipRole(
        membership_id=membership.id,
        role_id=staff_role.id,
    )
    db.add(membership_role)

    # 7. Commit changes and refresh user
    db.commit()
    db.refresh(user)

    # Attach roles for schema response serialization
    setattr(user, "roles", [RoleEnum.STAFF.value])
    return user


def get_user(db: Session, user_id: uuid.UUID, org_id: uuid.UUID) -> User:
    """Retrieve user and verify membership in the given organization.

    Raises 404 if user not found, 403 if not associated with organization.
    """
    user = (
        db.query(User)
        .options(
            selectinload(User.memberships)
            .selectinload(Membership.membership_roles)
            .joinedload(MembershipRole.role)
        )
        .filter(User.id == user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{user_id}' not found.",
        )

    membership = next(
        (m for m in user.memberships if m.organization_id == org_id),
        None,
    )

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a member of this organization.",
        )

    roles = [
        mr.role.name
        for mr in membership.membership_roles
        if mr.role and mr.role.name
    ]
    setattr(user, "roles", roles)
    return user


def update_user(
    db: Session,
    user_id: uuid.UUID,
    org_id: uuid.UUID,
    update_data: Union[dict[str, Any], Any],
) -> User:
    """Update user information (e.g., full_name, is_active) within an organization."""
    user = get_user(db, user_id, org_id)

    data: dict[str, Any]
    if hasattr(update_data, "model_dump"):
        data = update_data.model_dump(exclude_unset=True)
    elif isinstance(update_data, dict):
        data = update_data
    else:
        data = dict(update_data)

    modified = False
    if "full_name" in data and data["full_name"] is not None:
        name = str(data["full_name"]).strip()
        if name:
            user.full_name = name
            modified = True

    if "is_active" in data and data["is_active"] is not None:
        user.is_active = bool(data["is_active"])
        modified = True

    if modified:
        db.commit()
        db.refresh(user)

    # Re-retrieve user with org roles populated
    return get_user(db, user_id, org_id)


def deactivate_user(db: Session, user_id: uuid.UUID, org_id: uuid.UUID) -> dict[str, str]:
    """Deactivate a user's membership in an organization without deleting user record."""
    membership = (
        db.query(Membership)
        .filter(
            Membership.user_id == user_id,
            Membership.organization_id == org_id,
        )
        .first()
    )

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Membership for this user in the specified organization not found.",
        )

    membership.status = "inactive"
    db.commit()

    return {"message": "User membership deactivated successfully."}
