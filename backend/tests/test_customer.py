"""Customer management endpoint tests for VERISUB."""

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
    org = reg_data.get("organization", {})
    return str(org.get("id", ""))


def _setup_with_customer(client: TestClient) -> tuple[str, str, str]:
    """Register, create a customer, return (token, org_id, customer_id)."""
    reg_data = register_and_login(client)
    token = reg_data["access_token"]
    org_id = _get_org_id(reg_data)

    cust_resp = client.post(
        "/api/v1/customers/",
        headers=auth_headers(token, org_id),
        json={
            "customer_code": "CUST001",
            "company_name": "Acme Corp",
            "contact_name": "John Doe",
            "email": "john@acme.com",
            "phone": "+1234567890",
        },
    )
    assert cust_resp.status_code == 201
    customer_id = cust_resp.json()["id"]
    return token, org_id, customer_id


class TestCustomerCreate:
    """Tests for POST /api/v1/customers/."""

    def test_create_customer_success(self, client: TestClient):
        reg_data = register_and_login(client)
        token = reg_data["access_token"]
        org_id = _get_org_id(reg_data)

        resp = client.post(
            "/api/v1/customers/",
            headers=auth_headers(token, org_id),
            json={
                "customer_code": "CUST001",
                "company_name": "Acme Corp",
                "contact_name": "John",
                "email": "john@acme.com",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["customer_code"] == "CUST001"
        assert data["company_name"] == "Acme Corp"
        assert data["status"] == "active"

    def test_create_customer_duplicate_code(self, client: TestClient):
        token, org_id, _ = _setup_with_customer(client)
        resp = client.post(
            "/api/v1/customers/",
            headers=auth_headers(token, org_id),
            json={
                "customer_code": "CUST001",
                "company_name": "Other Corp",
            },
        )
        assert resp.status_code == 409

    def test_create_customer_missing_fields(self, client: TestClient):
        reg_data = register_and_login(client)
        token = reg_data["access_token"]
        org_id = _get_org_id(reg_data)
        resp = client.post(
            "/api/v1/customers/",
            headers=auth_headers(token, org_id),
            json={"company_name": "No Code"},
        )
        assert resp.status_code == 422

    def test_create_customer_unauthenticated(self, client: TestClient):
        resp = client.post(
            "/api/v1/customers/",
            json={"customer_code": "X", "company_name": "Y"},
        )
        assert resp.status_code in (401, 403)


class TestCustomerList:
    """Tests for GET /api/v1/customers/."""

    def test_list_customers(self, client: TestClient):
        token, org_id, _ = _setup_with_customer(client)
        resp = client.get(
            "/api/v1/customers/",
            headers=auth_headers(token, org_id),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        assert len(data["items"]) >= 1

    def test_list_customers_pagination(self, client: TestClient):
        reg_data = register_and_login(client)
        token = reg_data["access_token"]
        org_id = _get_org_id(reg_data)

        for i in range(5):
            client.post(
                "/api/v1/customers/",
                headers=auth_headers(token, org_id),
                json={
                    "customer_code": f"C{i:03d}",
                    "company_name": f"Company {i}",
                },
            )

        resp = client.get(
            "/api/v1/customers/?page=1&page_size=2",
            headers=auth_headers(token, org_id),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["page_size"] == 2
        assert len(data["items"]) == 2
        assert data["total"] == 5

    def test_list_customers_search(self, client: TestClient):
        token, org_id, _ = _setup_with_customer(client)

        # Add another customer
        client.post(
            "/api/v1/customers/",
            headers=auth_headers(token, org_id),
            json={"customer_code": "CUST002", "company_name": "Zenith Inc"},
        )

        resp = client.get(
            "/api/v1/customers/?search=Acme",
            headers=auth_headers(token, org_id),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        assert any("Acme" in c["company_name"] for c in data["items"])

    def test_list_customers_status_filter(self, client: TestClient):
        token, org_id, _ = _setup_with_customer(client)
        resp = client.get(
            "/api/v1/customers/?status=active",
            headers=auth_headers(token, org_id),
        )
        assert resp.status_code == 200
        for item in resp.json()["items"]:
            assert item["status"] == "active"


class TestCustomerGet:
    """Tests for GET /api/v1/customers/{customer_id}."""

    def test_get_customer_success(self, client: TestClient):
        token, org_id, customer_id = _setup_with_customer(client)
        resp = client.get(
            f"/api/v1/customers/{customer_id}",
            headers=auth_headers(token, org_id),
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == customer_id

    def test_get_customer_not_found(self, client: TestClient):
        reg_data = register_and_login(client)
        token = reg_data["access_token"]
        org_id = _get_org_id(reg_data)
        fake_id = str(uuid.uuid4())
        resp = client.get(
            f"/api/v1/customers/{fake_id}",
            headers=auth_headers(token, org_id),
        )
        assert resp.status_code == 404


class TestCustomerUpdate:
    """Tests for PATCH /api/v1/customers/{customer_id}."""

    def test_update_customer(self, client: TestClient):
        token, org_id, customer_id = _setup_with_customer(client)
        resp = client.patch(
            f"/api/v1/customers/{customer_id}",
            headers=auth_headers(token, org_id),
            json={"company_name": "Acme Updated"},
        )
        assert resp.status_code == 200
        assert resp.json()["company_name"] == "Acme Updated"

    def test_update_customer_status(self, client: TestClient):
        token, org_id, customer_id = _setup_with_customer(client)
        resp = client.patch(
            f"/api/v1/customers/{customer_id}",
            headers=auth_headers(token, org_id),
            json={"status": "suspended"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "suspended"


class TestCustomerDelete:
    """Tests for DELETE /api/v1/customers/{customer_id}."""

    def test_soft_delete_customer(self, client: TestClient):
        token, org_id, customer_id = _setup_with_customer(client)
        resp = client.delete(
            f"/api/v1/customers/{customer_id}",
            headers=auth_headers(token, org_id),
        )
        assert resp.status_code == 200

        # Should still exist but with inactive status
        get_resp = client.get(
            f"/api/v1/customers/{customer_id}",
            headers=auth_headers(token, org_id),
        )
        assert get_resp.status_code == 200
        assert get_resp.json()["status"] == "inactive"
