"""RBAC, organization isolation, and user management tests for VERISUB."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from backend.tests.conftest import (
    REGISTER_PAYLOAD,
    VALID_PASSWORD,
    auth_headers,
    register_and_login,
)


def _get_org_id(reg_data: dict) -> str:
    """Extract organization ID from registration response."""
    org = reg_data.get("organization", {})
    return str(org.get("id", ""))


# ── Admin permissions ────────────────────────────────────────────────
class TestAdminPermissions:
    """Tests that ADMIN role has full access."""

    def test_admin_can_list_users(self, client: TestClient):
        reg_data = register_and_login(client)
        token = reg_data["access_token"]
        org_id = _get_org_id(reg_data)
        resp = client.get(
            "/api/v1/users/",
            headers=auth_headers(token, org_id),
        )
        assert resp.status_code == 200

    def test_admin_can_create_staff(self, client: TestClient):
        reg_data = register_and_login(client)
        token = reg_data["access_token"]
        org_id = _get_org_id(reg_data)
        resp = client.post(
            "/api/v1/users/staff",
            headers=auth_headers(token, org_id),
            json={
                "full_name": "Staff User",
                "email": "staff@testco.com",
                "password": VALID_PASSWORD,
            },
        )
        assert resp.status_code == 201

    def test_admin_can_view_organization(self, client: TestClient):
        reg_data = register_and_login(client)
        token = reg_data["access_token"]
        org_id = _get_org_id(reg_data)
        resp = client.get(
            "/api/v1/organizations/current",
            headers=auth_headers(token, org_id),
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "TestCo"

    def test_admin_can_update_organization(self, client: TestClient):
        reg_data = register_and_login(client)
        token = reg_data["access_token"]
        org_id = _get_org_id(reg_data)
        resp = client.patch(
            "/api/v1/organizations/current",
            headers=auth_headers(token, org_id),
            json={"name": "UpdatedCo"},
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "UpdatedCo"

    def test_admin_can_manage_customers(self, client: TestClient):
        reg_data = register_and_login(client)
        token = reg_data["access_token"]
        org_id = _get_org_id(reg_data)
        resp = client.post(
            "/api/v1/customers/",
            headers=auth_headers(token, org_id),
            json={
                "customer_code": "CUST001",
                "company_name": "Customer Corp",
                "email": "contact@customercorp.com",
            },
        )
        assert resp.status_code == 201


# ── Staff restrictions ───────────────────────────────────────────────
class TestStaffRestrictions:
    """Tests that STAFF role has limited access."""

    def _create_staff_and_login(self, client: TestClient) -> tuple[str, str]:
        """Create a staff user and return (access_token, org_id)."""
        reg_data = register_and_login(client)
        admin_token = reg_data["access_token"]
        org_id = _get_org_id(reg_data)

        # Admin creates staff
        client.post(
            "/api/v1/users/staff",
            headers=auth_headers(admin_token, org_id),
            json={
                "full_name": "Staff User",
                "email": "staff@testco.com",
                "password": VALID_PASSWORD,
            },
        )

        # Staff logs in
        login_resp = client.post(
            "/api/v1/auth/login",
            json={
                "email": "staff@testco.com",
                "password": VALID_PASSWORD,
                "organization_id": org_id,
            },
        )
        assert login_resp.status_code == 200
        staff_data = login_resp.json()
        return staff_data["access_token"], org_id

    def test_staff_cannot_create_staff(self, client: TestClient):
        staff_token, org_id = self._create_staff_and_login(client)
        resp = client.post(
            "/api/v1/users/staff",
            headers=auth_headers(staff_token, org_id),
            json={
                "full_name": "Another Staff",
                "email": "staff2@testco.com",
                "password": VALID_PASSWORD,
            },
        )
        assert resp.status_code == 403

    def test_staff_cannot_update_organization(self, client: TestClient):
        staff_token, org_id = self._create_staff_and_login(client)
        resp = client.patch(
            "/api/v1/organizations/current",
            headers=auth_headers(staff_token, org_id),
            json={"name": "HackedCo"},
        )
        assert resp.status_code == 403

    def test_staff_can_manage_customers(self, client: TestClient):
        staff_token, org_id = self._create_staff_and_login(client)
        resp = client.post(
            "/api/v1/customers/",
            headers=auth_headers(staff_token, org_id),
            json={
                "customer_code": "CUST001",
                "company_name": "Customer Corp",
            },
        )
        assert resp.status_code == 201

    def test_staff_can_list_customers(self, client: TestClient):
        staff_token, org_id = self._create_staff_and_login(client)
        resp = client.get(
            "/api/v1/customers/",
            headers=auth_headers(staff_token, org_id),
        )
        assert resp.status_code == 200


# ── Cross-organization isolation ─────────────────────────────────────
class TestOrganizationIsolation:
    """Tests that data is isolated between organizations."""

    def test_cannot_access_other_org_customers(self, client: TestClient):
        # Register org 1
        reg1 = register_and_login(client)
        token1 = reg1["access_token"]
        org1_id = _get_org_id(reg1)

        # Create a customer in org 1
        cust_resp = client.post(
            "/api/v1/customers/",
            headers=auth_headers(token1, org1_id),
            json={"customer_code": "C001", "company_name": "Org1 Customer"},
        )
        assert cust_resp.status_code == 201
        customer_id = cust_resp.json()["id"]

        # Register org 2
        payload2 = {
            "organization_name": "OtherCo",
            "organization_email": "other@co.com",
            "admin_full_name": "Other Admin",
            "admin_email": "admin@otherco.com",
            "admin_password": VALID_PASSWORD,
        }
        reg2 = register_and_login(client, payload2)
        token2 = reg2["access_token"]
        org2_id = _get_org_id(reg2)

        # Try to access org1's customer from org2
        resp = client.get(
            f"/api/v1/customers/{customer_id}",
            headers=auth_headers(token2, org2_id),
        )
        assert resp.status_code == 404

    def test_cannot_list_other_org_customers(self, client: TestClient):
        # Register org 1 with a customer
        reg1 = register_and_login(client)
        token1 = reg1["access_token"]
        org1_id = _get_org_id(reg1)
        client.post(
            "/api/v1/customers/",
            headers=auth_headers(token1, org1_id),
            json={"customer_code": "C001", "company_name": "Org1 Customer"},
        )

        # Register org 2
        payload2 = {
            "organization_name": "OtherCo",
            "organization_email": "other@co.com",
            "admin_full_name": "Other Admin",
            "admin_email": "admin@otherco.com",
            "admin_password": VALID_PASSWORD,
        }
        reg2 = register_and_login(client, payload2)
        token2 = reg2["access_token"]
        org2_id = _get_org_id(reg2)

        # List customers from org2 — should be empty
        resp = client.get(
            "/api/v1/customers/",
            headers=auth_headers(token2, org2_id),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert len(data["items"]) == 0

    def test_cannot_access_other_org_with_forged_header(self, client: TestClient):
        # Register org 1
        reg1 = register_and_login(client)
        token1 = reg1["access_token"]
        org1_id = _get_org_id(reg1)

        # Register org 2
        payload2 = {
            "organization_name": "OtherCo",
            "organization_email": "other@co.com",
            "admin_full_name": "Other Admin",
            "admin_email": "admin@otherco.com",
            "admin_password": VALID_PASSWORD,
        }
        reg2 = register_and_login(client, payload2)
        org2_id = _get_org_id(reg2)

        # User from org1 tries to use org2's ID in headers
        resp = client.get(
            "/api/v1/users/",
            headers=auth_headers(token1, org2_id),
        )
        assert resp.status_code == 403


# ── User management ──────────────────────────────────────────────────
class TestUserManagement:
    """Tests for user CRUD operations."""

    def test_list_users_pagination(self, client: TestClient):
        reg_data = register_and_login(client)
        token = reg_data["access_token"]
        org_id = _get_org_id(reg_data)

        # Create some staff users
        for i in range(3):
            client.post(
                "/api/v1/users/staff",
                headers=auth_headers(token, org_id),
                json={
                    "full_name": f"Staff {i}",
                    "email": f"staff{i}@testco.com",
                    "password": VALID_PASSWORD,
                },
            )

        resp = client.get(
            "/api/v1/users/?page=1&page_size=2",
            headers=auth_headers(token, org_id),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["page"] == 1
        assert data["page_size"] == 2
        assert data["total"] >= 4  # admin + 3 staff

    def test_get_user_by_id(self, client: TestClient):
        reg_data = register_and_login(client)
        token = reg_data["access_token"]
        org_id = _get_org_id(reg_data)

        # Create staff
        staff_resp = client.post(
            "/api/v1/users/staff",
            headers=auth_headers(token, org_id),
            json={
                "full_name": "Staff User",
                "email": "staff@testco.com",
                "password": VALID_PASSWORD,
            },
        )
        staff_id = staff_resp.json()["id"]

        resp = client.get(
            f"/api/v1/users/{staff_id}",
            headers=auth_headers(token, org_id),
        )
        assert resp.status_code == 200
        assert resp.json()["email"] == "staff@testco.com"

    def test_deactivate_user(self, client: TestClient):
        reg_data = register_and_login(client)
        token = reg_data["access_token"]
        org_id = _get_org_id(reg_data)

        # Create staff
        staff_resp = client.post(
            "/api/v1/users/staff",
            headers=auth_headers(token, org_id),
            json={
                "full_name": "Staff User",
                "email": "staff@testco.com",
                "password": VALID_PASSWORD,
            },
        )
        staff_id = staff_resp.json()["id"]

        # Deactivate
        resp = client.delete(
            f"/api/v1/users/{staff_id}",
            headers=auth_headers(token, org_id),
        )
        assert resp.status_code == 200

    def test_create_staff_duplicate_email(self, client: TestClient):
        reg_data = register_and_login(client)
        token = reg_data["access_token"]
        org_id = _get_org_id(reg_data)

        staff_payload = {
            "full_name": "Staff User",
            "email": "staff@testco.com",
            "password": VALID_PASSWORD,
        }
        client.post(
            "/api/v1/users/staff",
            headers=auth_headers(token, org_id),
            json=staff_payload,
        )
        resp = client.post(
            "/api/v1/users/staff",
            headers=auth_headers(token, org_id),
            json=staff_payload,
        )
        assert resp.status_code == 409
