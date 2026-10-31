"""Permission and Role definitions and role-permission mappings."""

from enum import Enum


class PermissionEnum(str, Enum):
    """Atomic permissions supported across the platform."""

    MANAGE_ORGANIZATION = "MANAGE_ORGANIZATION"
    MANAGE_STAFF = "MANAGE_STAFF"
    MANAGE_CUSTOMERS = "MANAGE_CUSTOMERS"
    MANAGE_PRODUCTS = "MANAGE_PRODUCTS"
    MANAGE_PLANS = "MANAGE_PLANS"
    MANAGE_SUBSCRIPTIONS = "MANAGE_SUBSCRIPTIONS"
    MANAGE_BILLING = "MANAGE_BILLING"
    VIEW_REPORTS = "VIEW_REPORTS"
    MANAGE_SETTINGS = "MANAGE_SETTINGS"
    VIEW_OWN_SUBSCRIPTIONS = "VIEW_OWN_SUBSCRIPTIONS"
    VIEW_OWN_INVOICES = "VIEW_OWN_INVOICES"
    VIEW_OWN_PAYMENTS = "VIEW_OWN_PAYMENTS"

    @classmethod
    def _missing_(cls, value: object):
        if isinstance(value, str):
            for member in cls:
                if member.value.lower() == value.lower():
                    return member
        return None


class RoleEnum(str, Enum):
    """Standard system roles."""

    ADMIN = "ADMIN"
    STAFF = "STAFF"
    CUSTOMER = "CUSTOMER"

    @classmethod
    def _missing_(cls, value: object):
        if isinstance(value, str):
            for member in cls:
                if member.value.lower() == value.lower():
                    return member
        return None


ROLE_PERMISSIONS: dict[RoleEnum, list[PermissionEnum]] = {
    RoleEnum.ADMIN: list(PermissionEnum),
    RoleEnum.STAFF: [
        PermissionEnum.MANAGE_CUSTOMERS,
        PermissionEnum.MANAGE_PRODUCTS,
        PermissionEnum.MANAGE_PLANS,
        PermissionEnum.MANAGE_SUBSCRIPTIONS,
        PermissionEnum.MANAGE_BILLING,
        PermissionEnum.VIEW_REPORTS,
    ],
    RoleEnum.CUSTOMER: [
        PermissionEnum.VIEW_OWN_SUBSCRIPTIONS,
        PermissionEnum.VIEW_OWN_INVOICES,
        PermissionEnum.VIEW_OWN_PAYMENTS,
    ],
}


DEFAULT_PERMISSIONS: list[tuple[PermissionEnum, str]] = [
    (PermissionEnum.MANAGE_ORGANIZATION, "Manage organization details, profile, and settings"),
    (PermissionEnum.MANAGE_STAFF, "Manage staff members, roles, and invitations"),
    (PermissionEnum.MANAGE_CUSTOMERS, "Create, view, update, and manage customer records"),
    (PermissionEnum.MANAGE_PRODUCTS, "Create, update, and manage product catalog"),
    (PermissionEnum.MANAGE_PLANS, "Create, update, and manage subscription pricing plans"),
    (PermissionEnum.MANAGE_SUBSCRIPTIONS, "Create, modify, pause, resume, and cancel subscriptions"),
    (PermissionEnum.MANAGE_BILLING, "Manage billing, invoices, payment methods, and transactions"),
    (PermissionEnum.VIEW_REPORTS, "Access business analytics, revenue reports, and platform metrics"),
    (PermissionEnum.MANAGE_SETTINGS, "Configure platform-wide and organization-level settings"),
    (PermissionEnum.VIEW_OWN_SUBSCRIPTIONS, "View customer own subscription details and status"),
    (PermissionEnum.VIEW_OWN_INVOICES, "View and download customer own invoices"),
    (PermissionEnum.VIEW_OWN_PAYMENTS, "View customer own payment history and receipts"),
]
