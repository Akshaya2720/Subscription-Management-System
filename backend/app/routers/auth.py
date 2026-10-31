"""Authentication and user session router for VERISUB."""

from __future__ import annotations

from typing import Any
import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.dependencies.auth import get_current_user
from backend.app.models.user import User
from backend.app.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    UpdateProfileRequest,
    UserProfileResponse,
)
from backend.app.schemas.common import MessageResponse
from backend.app.services import auth_service

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    summary="Register a new organization and admin account",
)
def register(
    payload: RegisterRequest,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Register a new tenant organization and its initial administrator user.

    Issues initial scoped JWT access and refresh tokens upon successful onboarding.
    No authentication is required.
    """
    return auth_service.register_organization(
        db=db,
        org_name=payload.organization_name,
        org_email=payload.organization_email,
        org_phone=payload.organization_phone,
        org_industry=payload.organization_industry,
        admin_name=payload.admin_full_name,
        admin_email=payload.admin_email,
        admin_password=payload.admin_password,
    )


@router.post(
    "/login",
    summary="Authenticate user and issue scoped access tokens",
)
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Authenticate user credentials and issue scoped access and refresh tokens.

    If the user belongs to multiple active organizations and none is specified,
    returns organization options for context selection.
    No authentication is required.
    """
    return auth_service.login(
        db=db,
        email=payload.email,
        password=payload.password,
        organization_id=payload.organization_id,
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token using valid refresh token",
)
def refresh(
    payload: RefreshRequest,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Rotate refresh token and issue a fresh JWT access token.

    No authentication header required.
    """
    return auth_service.refresh_access_token(
        db=db,
        refresh_token_str=payload.refresh_token,
    )


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Revoke refresh token and end session",
)
def logout(
    payload: RefreshRequest,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Revoke an active refresh token to end the user session.

    No authentication header required.
    """
    return auth_service.logout(
        db=db,
        refresh_token_str=payload.refresh_token,
    )


@router.post(
    "/forgot-password",
    response_model=ForgotPasswordResponse,
    summary="Request password reset instructions",
)
def forgot_password(
    payload: ForgotPasswordRequest,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Initiate password reset flow for a registered email address.

    Sends reset token via email or returns it directly in development mode.
    No authentication required.
    """
    return auth_service.forgot_password(
        db=db,
        email=payload.email,
    )


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    summary="Reset password using reset token",
)
def reset_password(
    payload: ResetPasswordRequest,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Reset user password using a verified single-use reset token.

    No authentication required.
    """
    return auth_service.reset_password(
        db=db,
        token=payload.token,
        new_password=payload.new_password,
    )


@router.get(
    "/me",
    response_model=UserProfileResponse,
    summary="Retrieve current user profile and memberships",
)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    """Retrieve full user profile and associated organizations for the authenticated user.

    Requires valid Bearer token.
    """
    return auth_service.get_user_profile(
        db=db,
        user_id=current_user.id,
    )


@router.patch(
    "/me",
    response_model=UserProfileResponse,
    summary="Update current user profile information",
)
def update_current_user_profile(
    payload: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    """Update personal profile fields (e.g., full_name) for the authenticated user.

    Requires valid Bearer token.
    """
    return auth_service.update_user_profile(
        db=db,
        user_id=current_user.id,
        full_name=payload.full_name,
    )


@router.post(
    "/change-password",
    response_model=MessageResponse,
    summary="Change user password",
)
def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Change current user's password after verifying existing password.

    Invalidates all existing refresh tokens to force re-authentication.
    Requires valid Bearer token.
    """
    return auth_service.change_password(
        db=db,
        user_id=current_user.id,
        current_password=payload.current_password,
        new_password=payload.new_password,
    )
