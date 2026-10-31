"""Authentication and account management service for VERISUB."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import logging
import secrets
from typing import Any, Optional
import uuid

from fastapi import HTTPException, status
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session, joinedload, selectinload

from backend.app.core.config import settings
from backend.app.core.permissions import (
    DEFAULT_PERMISSIONS,
    ROLE_PERMISSIONS,
    PermissionEnum,
    RoleEnum,
)
from backend.app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_reset_token,
    hash_password,
    hash_token,
    validate_password,
    verify_password,
)
from backend.app.models.membership import Membership
from backend.app.models.organization import Organization, OrganizationSettings
from backend.app.models.role import MembershipRole, Permission, Role, RolePermission
from backend.app.models.token import PasswordResetToken, RefreshToken
from backend.app.models.user import User

logger = logging.getLogger(__name__)


def _ensure_roles_and_permissions(db: Session) -> dict[str, Role]:
    """Ensure standard roles, permissions, and role-permission mappings exist.

    Idempotent helper function. Flushes modifications without committing.
    """
    # 1. Ensure all standard roles exist
    roles_by_name: dict[str, Role] = {}
    for role_enum in RoleEnum:
        role_name = role_enum.value
        role = db.query(Role).filter(Role.name == role_name).first()
        if not role:
            role = Role(
                name=role_name,
                description=f"{role_name.capitalize()} system role",
            )
            db.add(role)
            db.flush()
        roles_by_name[role_name] = role

    # 2. Ensure all standard permissions exist
    permissions_by_name: dict[str, Permission] = {}
    for perm_enum, description in DEFAULT_PERMISSIONS:
        perm_name = perm_enum.value
        perm = db.query(Permission).filter(Permission.permission_name == perm_name).first()
        if not perm:
            perm = Permission(
                permission_name=perm_name,
                description=description,
            )
            db.add(perm)
            db.flush()
        permissions_by_name[perm_name] = perm

    # 3. Ensure role-permission associations exist
    for role_enum, perm_enums in ROLE_PERMISSIONS.items():
        role = roles_by_name[role_enum.value]
        existing_rp = (
            db.query(RolePermission.permission_id)
            .filter(RolePermission.role_id == role.id)
            .all()
        )
        existing_perm_ids = {rp[0] for rp in existing_rp}

        for perm_enum in perm_enums:
            perm = permissions_by_name.get(perm_enum.value)
            if perm and perm.id not in existing_perm_ids:
                new_rp = RolePermission(role_id=role.id, permission_id=perm.id)
                db.add(new_rp)
                existing_perm_ids.add(perm.id)

    db.flush()
    return roles_by_name


def register_organization(
    db: Session,
    org_name: str,
    org_email: str,
    org_phone: Optional[str],
    org_industry: Optional[str],
    admin_name: str,
    admin_email: str,
    admin_password: str,
) -> dict[str, Any]:
    """Register a new tenant organization and its initial administrator account."""
    # 1. Validate administrator password complexity
    is_valid, error_msg = validate_password(admin_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg,
        )

    norm_org_email = org_email.strip().lower()
    norm_admin_email = admin_email.strip().lower()

    # 2. Check if organization email is already registered
    existing_org = db.query(Organization).filter(Organization.email == norm_org_email).first()
    if existing_org:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Organization with this email is already registered.",
        )

    # 3. Check if admin email is already registered
    existing_user = db.query(User).filter(User.email == norm_admin_email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email is already registered.",
        )

    # 4. Create Organization
    organization = Organization(
        name=org_name.strip(),
        email=norm_org_email,
        phone=org_phone.strip() if org_phone else None,
        industry=org_industry.strip() if org_industry else None,
        status="active",
    )
    db.add(organization)
    db.flush()

    # 5. Create OrganizationSettings with defaults
    org_settings = OrganizationSettings(
        organization_id=organization.id,
        default_currency="USD",
        timezone="UTC",
    )
    db.add(org_settings)

    # 6. Create initial User
    user = User(
        full_name=admin_name.strip(),
        email=norm_admin_email,
        password_hash=hash_password(admin_password),
        is_active=True,
        email_verified=False,
    )
    db.add(user)
    db.flush()

    # 7. Create Membership
    membership = Membership(
        organization_id=organization.id,
        user_id=user.id,
        status="active",
    )
    db.add(membership)
    db.flush()

    # 8. Ensure standard roles and assign ADMIN role to membership
    roles_map = _ensure_roles_and_permissions(db)
    admin_role = roles_map.get(RoleEnum.ADMIN.value)
    if not admin_role:
        admin_role = db.query(Role).filter(Role.name == RoleEnum.ADMIN.value).first()

    membership_role = MembershipRole(
        membership_id=membership.id,
        role_id=admin_role.id,
    )
    db.add(membership_role)

    # Commit the foundational setup
    db.commit()
    db.refresh(user)
    db.refresh(organization)

    # 9. Generate access & refresh tokens
    access_claims = {
        "sub": str(user.id),
        "org_id": str(organization.id),
    }
    refresh_claims = {
        "sub": str(user.id),
        "org_id": str(organization.id),
        "jti": str(uuid.uuid4()),
    }
    access_token = create_access_token(access_claims)
    refresh_token = create_refresh_token(refresh_claims)

    # 10. Persist hashed refresh token
    token_hash = hash_token(refresh_token)
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_record = RefreshToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
    )
    db.add(refresh_record)
    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "full_name": user.full_name,
            "email": user.email,
        },
        "organization": {
            "id": organization.id,
            "name": organization.name,
            "email": organization.email,
        },
    }


def login(
    db: Session,
    email: str,
    password: str,
    organization_id: Optional[uuid.UUID] = None,
) -> dict[str, Any]:
    """Authenticate user credentials and issue scoped access tokens."""
    norm_email = email.strip().lower()
    user = db.query(User).filter(User.email == norm_email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    if not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated.",
        )

    active_memberships = (
        db.query(Membership)
        .options(
            joinedload(Membership.organization),
            selectinload(Membership.membership_roles).joinedload(MembershipRole.role),
        )
        .filter(
            Membership.user_id == user.id,
            Membership.status == "active",
        )
        .all()
    )

    if not active_memberships:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have an active membership in any organization.",
        )

    selected_membership: Optional[Membership] = None

    if organization_id:
        selected_membership = next(
            (m for m in active_memberships if m.organization_id == organization_id),
            None,
        )
        if not selected_membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is not an active member of the specified organization.",
            )
    elif len(active_memberships) == 1:
        selected_membership = active_memberships[0]
    else:
        # Prompt user to select organization
        return {
            "requires_organization_selection": True,
            "user": {
                "id": user.id,
                "full_name": user.full_name,
                "email": user.email,
            },
            "organizations": [
                {
                    "id": m.organization.id,
                    "name": m.organization.name,
                    "email": m.organization.email,
                    "roles": [mr.role.name for mr in m.membership_roles if mr.role],
                }
                for m in active_memberships
            ],
        }

    access_claims = {
        "sub": str(user.id),
        "org_id": str(selected_membership.organization_id),
    }
    refresh_claims = {
        "sub": str(user.id),
        "org_id": str(selected_membership.organization_id),
        "jti": str(uuid.uuid4()),
    }
    access_token = create_access_token(access_claims)
    refresh_token = create_refresh_token(refresh_claims)

    token_hash = hash_token(refresh_token)
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_record = RefreshToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
    )
    db.add(refresh_record)
    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "full_name": user.full_name,
            "email": user.email,
        },
        "organization": {
            "id": selected_membership.organization.id,
            "name": selected_membership.organization.name,
            "email": selected_membership.organization.email,
        },
    }


def refresh_access_token(db: Session, refresh_token_str: str) -> dict[str, Any]:
    """Rotate refresh token and issue a fresh access token."""
    try:
        payload = decode_token(refresh_token_str)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired refresh token: {e}",
        )

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Provided token is not a refresh token.",
        )

    user_id_str = payload.get("sub")
    org_id_str = payload.get("org_id")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token subject missing.",
        )

    token_hash = hash_token(refresh_token_str)
    now = datetime.now(timezone.utc)

    token_record = (
        db.query(RefreshToken)
        .filter(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked_at.is_(None),
            RefreshToken.expires_at > now,
        )
        .first()
    )

    if not token_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired or been revoked.",
        )

    try:
        user_uuid = uuid.UUID(user_id_str)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in token.",
        )

    user = db.query(User).filter(User.id == user_uuid).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive or not found.",
        )

    if org_id_str:
        try:
            org_uuid = uuid.UUID(org_id_str)
            membership = (
                db.query(Membership)
                .filter(
                    Membership.user_id == user_uuid,
                    Membership.organization_id == org_uuid,
                    Membership.status == "active",
                )
                .first()
            )
            if not membership:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User is not an active member of this organization.",
                )
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid organization ID in token.",
            )

    # Invalidate previous refresh token
    token_record.revoked_at = now

    new_access_claims = {
        "sub": user_id_str,
    }
    new_refresh_claims = {
        "sub": user_id_str,
        "jti": str(uuid.uuid4()),
    }
    if org_id_str:
        new_access_claims["org_id"] = org_id_str
        new_refresh_claims["org_id"] = org_id_str

    new_access_token = create_access_token(new_access_claims)
    new_refresh_token = create_refresh_token(new_refresh_claims)

    new_hash = hash_token(new_refresh_token)
    new_expires_at = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    new_record = RefreshToken(
        user_id=user.id,
        token_hash=new_hash,
        expires_at=new_expires_at,
    )
    db.add(new_record)
    db.commit()

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }


def logout(db: Session, refresh_token_str: str) -> dict[str, str]:
    """Revoke a refresh token to end the active session."""
    token_hash = hash_token(refresh_token_str)
    record = (
        db.query(RefreshToken)
        .filter(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked_at.is_(None),
        )
        .first()
    )
    if record:
        record.revoked_at = datetime.now(timezone.utc)
        db.commit()

    return {"message": "Logged out successfully."}


def forgot_password(db: Session, email: str) -> dict[str, Any]:
    """Initiate password reset flow for a user email address."""
    norm_email = email.strip().lower()
    user = db.query(User).filter(User.email == norm_email).first()

    # Generic response if user is not found to prevent user enumeration
    if not user:
        return {
            "message": "If this email is registered, password reset instructions have been sent.",
            "reset_token": None,
        }

    plain_token, hashed_token = generate_reset_token()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

    reset_token_record = PasswordResetToken(
        user_id=user.id,
        token_hash=hashed_token,
        expires_at=expires_at,
    )
    db.add(reset_token_record)
    db.commit()

    if settings.smtp_configured:
        logger.info(
            "SMTP configured: Password reset link would be dispatched to %s with token %s",
            user.email,
            plain_token,
        )
        return {
            "message": "If this email is registered, password reset instructions have been sent.",
            "reset_token": None,
        }

    # Development mode fallback: return plain reset token directly
    return {
        "message": (
            "Password reset token generated. In development mode without SMTP, "
            "the token is returned directly."
        ),
        "reset_token": plain_token,
    }


def reset_password(db: Session, token: str, new_password: str) -> dict[str, str]:
    """Reset user password using a verified single-use reset token."""
    is_valid, error_msg = validate_password(new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg,
        )

    token_hash = hash_token(token.strip())
    now = datetime.now(timezone.utc)

    reset_record = (
        db.query(PasswordResetToken)
        .filter(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.expires_at > now,
        )
        .first()
    )

    if not reset_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset token.",
        )

    user = db.query(User).filter(User.id == reset_record.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated user account not found.",
        )

    user.password_hash = hash_password(new_password)
    reset_record.used_at = now

    # Invalidate all active refresh tokens for security
    db.query(RefreshToken).filter(
        RefreshToken.user_id == user.id,
        RefreshToken.revoked_at.is_(None),
    ).update({"revoked_at": now}, synchronize_session=False)

    db.commit()
    return {"message": "Password has been successfully reset."}


def change_password(
    db: Session,
    user_id: uuid.UUID,
    current_password: str,
    new_password: str,
) -> dict[str, str]:
    """Change user password after verifying current password."""
    is_valid, error_msg = validate_password(new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg,
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    if not verify_password(current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect.",
        )

    now = datetime.now(timezone.utc)
    user.password_hash = hash_password(new_password)

    # Force re-authentication across all sessions
    db.query(RefreshToken).filter(
        RefreshToken.user_id == user.id,
        RefreshToken.revoked_at.is_(None),
    ).update({"revoked_at": now}, synchronize_session=False)

    db.commit()
    return {"message": "Password changed successfully."}


def get_user_profile(db: Session, user_id: uuid.UUID) -> User:
    """Retrieve full user profile with memberships, roles, and organizations."""
    user = (
        db.query(User)
        .options(
            selectinload(User.memberships).joinedload(Membership.organization),
            selectinload(User.memberships)
            .selectinload(Membership.membership_roles)
            .joinedload(MembershipRole.role),
        )
        .filter(User.id == user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    # Populate synthetic organizations attribute for schema serialization
    org_list = []
    for m in user.memberships:
        if m.organization:
            roles = [mr.role.name for mr in m.membership_roles if mr.role]
            org_list.append({
                "organization_id": m.organization.id,
                "organization_name": m.organization.name,
                "roles": roles,
                "status": m.status,
            })
    setattr(user, "organizations", org_list)
    return user


def update_user_profile(
    db: Session,
    user_id: uuid.UUID,
    full_name: Optional[str] = None,
) -> User:
    """Update personal profile fields for a user."""
    user = get_user_profile(db, user_id)
    if full_name is not None and full_name.strip():
        user.full_name = full_name.strip()
        db.commit()
        db.refresh(user)
        return get_user_profile(db, user_id)
    return user
