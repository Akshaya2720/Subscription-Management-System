"""Pydantic schemas package for VERISUB."""

from backend.app.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    OrganizationMembershipInfo,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    UpdateProfileRequest,
    UserProfileResponse,
)
from backend.app.schemas.common import MessageResponse, PaginatedResponse
from backend.app.schemas.customer import (
    CustomerAddressCreate,
    CustomerAddressResponse,
    CustomerContactCreate,
    CustomerContactResponse,
    CustomerCreate,
    CustomerDetailResponse,
    CustomerResponse,
    CustomerUpdate,
)
from backend.app.schemas.organization import (
    OrganizationCreate,
    OrganizationResponse,
    OrganizationSettingsResponse,
    OrganizationSettingsUpdate,
    OrganizationUpdate,
)
from backend.app.schemas.user import (
    CreateStaffRequest,
    UpdateUserRequest,
    UserResponse,
)

__all__ = [
    # Common
    "MessageResponse",
    "PaginatedResponse",
    # Auth
    "RegisterRequest",
    "LoginRequest",
    "TokenResponse",
    "RefreshRequest",
    "ForgotPasswordRequest",
    "ForgotPasswordResponse",
    "ResetPasswordRequest",
    "ChangePasswordRequest",
    "OrganizationMembershipInfo",
    "UserProfileResponse",
    "UpdateProfileRequest",
    # Organization
    "OrganizationCreate",
    "OrganizationUpdate",
    "OrganizationResponse",
    "OrganizationSettingsResponse",
    "OrganizationSettingsUpdate",
    # User
    "UserResponse",
    "CreateStaffRequest",
    "UpdateUserRequest",
    # Customer
    "CustomerCreate",
    "CustomerUpdate",
    "CustomerResponse",
    "CustomerAddressCreate",
    "CustomerAddressResponse",
    "CustomerContactCreate",
    "CustomerContactResponse",
    "CustomerDetailResponse",
]
