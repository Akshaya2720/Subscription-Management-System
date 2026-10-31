"""Business services package for VERISUB."""

from backend.app.services.auth_service import (
    change_password,
    forgot_password,
    get_user_profile,
    login,
    logout,
    refresh_access_token,
    register_organization,
    reset_password,
    update_user_profile,
)
from backend.app.services.customer_service import (
    add_customer_address,
    add_customer_contact,
    create_customer,
    delete_customer,
    get_customer,
    list_customers,
    update_customer,
)
from backend.app.services.organization_service import (
    get_organization,
    get_organization_settings,
    update_organization,
    update_organization_settings,
)
from backend.app.services.user_service import (
    create_staff_user,
    deactivate_user,
    get_user,
    list_users,
    update_user,
)

__all__ = [
    # Auth
    "register_organization",
    "login",
    "refresh_access_token",
    "logout",
    "forgot_password",
    "reset_password",
    "change_password",
    "get_user_profile",
    "update_user_profile",
    # Organization
    "get_organization",
    "update_organization",
    "get_organization_settings",
    "update_organization_settings",
    # User
    "list_users",
    "create_staff_user",
    "get_user",
    "update_user",
    "deactivate_user",
    # Customer
    "create_customer",
    "list_customers",
    "get_customer",
    "update_customer",
    "delete_customer",
    "add_customer_address",
    "add_customer_contact",
]
