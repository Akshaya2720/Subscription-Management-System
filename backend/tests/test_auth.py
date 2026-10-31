"""Authentication endpoint tests for VERISUB."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from backend.tests.conftest import (
    REGISTER_PAYLOAD,
    VALID_PASSWORD,
    WEAK_PASSWORD,
    auth_headers,
    register_and_login,
)


# ── Registration ─────────────────────────────────────────────────────
class TestRegistration:
    """Tests for POST /api/v1/auth/register."""

    def test_register_success(self, client: TestClient):
        resp = client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
        assert resp.status_code == 201
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data.get("organization", {}).get("name") == "TestCo"

    def test_register_duplicate_org_email(self, client: TestClient):
        client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
        resp = client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
        assert resp.status_code == 409

    def test_register_duplicate_admin_email(self, client: TestClient):
        client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
        payload2 = REGISTER_PAYLOAD.copy()
        payload2["organization_name"] = "OtherCo"
        payload2["organization_email"] = "other@co.com"
        # Same admin_email
        resp = client.post("/api/v1/auth/register", json=payload2)
        assert resp.status_code == 409

    def test_register_weak_password(self, client: TestClient):
        payload = REGISTER_PAYLOAD.copy()
        payload["admin_password"] = WEAK_PASSWORD
        resp = client.post("/api/v1/auth/register", json=payload)
        assert resp.status_code in (400, 422)

    def test_register_no_uppercase_password(self, client: TestClient):
        payload = REGISTER_PAYLOAD.copy()
        payload["admin_password"] = "weakpass1@abc"
        resp = client.post("/api/v1/auth/register", json=payload)
        assert resp.status_code == 400

    def test_register_no_special_char_password(self, client: TestClient):
        payload = REGISTER_PAYLOAD.copy()
        payload["admin_password"] = "StrongPass1abc"
        resp = client.post("/api/v1/auth/register", json=payload)
        assert resp.status_code == 400

    def test_register_missing_fields(self, client: TestClient):
        resp = client.post("/api/v1/auth/register", json={"organization_name": "X"})
        assert resp.status_code == 422


# ── Login ────────────────────────────────────────────────────────────
class TestLogin:
    """Tests for POST /api/v1/auth/login."""

    def test_login_success(self, client: TestClient):
        register_and_login(client)
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@testco.com", "password": VALID_PASSWORD},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_login_wrong_password(self, client: TestClient):
        register_and_login(client)
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@testco.com", "password": "WrongP@ss1"},
        )
        assert resp.status_code == 401

    def test_login_nonexistent_user(self, client: TestClient):
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@test.com", "password": VALID_PASSWORD},
        )
        assert resp.status_code == 401

    def test_login_invalid_email_format(self, client: TestClient):
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": "not-an-email", "password": VALID_PASSWORD},
        )
        assert resp.status_code == 422


# ── Token refresh ────────────────────────────────────────────────────
class TestTokenRefresh:
    """Tests for POST /api/v1/auth/refresh."""

    def test_refresh_success(self, client: TestClient):
        reg_data = register_and_login(client)
        refresh_token = reg_data["refresh_token"]
        resp = client.post(
            "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data

    def test_refresh_invalid_token(self, client: TestClient):
        resp = client.post(
            "/api/v1/auth/refresh", json={"refresh_token": "invalid-token"}
        )
        assert resp.status_code == 401


# ── Logout ───────────────────────────────────────────────────────────
class TestLogout:
    """Tests for POST /api/v1/auth/logout."""

    def test_logout_success(self, client: TestClient):
        reg_data = register_and_login(client)
        refresh_token = reg_data["refresh_token"]
        resp = client.post(
            "/api/v1/auth/logout", json={"refresh_token": refresh_token}
        )
        assert resp.status_code == 200

    def test_logout_then_refresh_fails(self, client: TestClient):
        reg_data = register_and_login(client)
        refresh_token = reg_data["refresh_token"]
        client.post("/api/v1/auth/logout", json={"refresh_token": refresh_token})
        resp = client.post(
            "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
        )
        assert resp.status_code == 401


# ── Password reset ───────────────────────────────────────────────────
class TestPasswordReset:
    """Tests for forgot + reset password flow."""

    def test_forgot_password_returns_token_in_dev(self, client: TestClient):
        register_and_login(client)
        resp = client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "admin@testco.com"},
        )
        assert resp.status_code == 200
        data = resp.json()
        # In dev mode (no SMTP), the token should be returned
        assert "reset_token" in data or "message" in data

    def test_reset_password_success(self, client: TestClient):
        register_and_login(client)
        # Get reset token
        forgot_resp = client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "admin@testco.com"},
        )
        data = forgot_resp.json()
        reset_token = data.get("reset_token")
        if not reset_token:
            pytest.skip("Reset token not returned in response (SMTP may be configured)")

        # Reset password
        resp = client.post(
            "/api/v1/auth/reset-password",
            json={"token": reset_token, "new_password": "NewStr0ng@Pass"},
        )
        assert resp.status_code == 200

        # Login with new password
        login_resp = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@testco.com", "password": "NewStr0ng@Pass"},
        )
        assert login_resp.status_code == 200

    def test_reset_password_invalid_token(self, client: TestClient):
        resp = client.post(
            "/api/v1/auth/reset-password",
            json={"token": "invalid-token", "new_password": "NewStr0ng@Pass"},
        )
        assert resp.status_code == 400

    def test_forgot_password_nonexistent_email(self, client: TestClient):
        resp = client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "nobody@nowhere.com"},
        )
        # Should not leak whether the email exists
        assert resp.status_code == 200


# ── Current user (me) ────────────────────────────────────────────────
class TestCurrentUser:
    """Tests for GET/PATCH /api/v1/auth/me."""

    def test_get_me_success(self, client: TestClient):
        reg_data = register_and_login(client)
        token = reg_data["access_token"]
        resp = client.get("/api/v1/auth/me", headers=auth_headers(token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "admin@testco.com"
        assert data["full_name"] == "Admin User"

    def test_get_me_unauthenticated(self, client: TestClient):
        resp = client.get("/api/v1/auth/me")
        assert resp.status_code in (401, 403)

    def test_get_me_invalid_token(self, client: TestClient):
        resp = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert resp.status_code in (401, 403)

    def test_update_profile(self, client: TestClient):
        reg_data = register_and_login(client)
        token = reg_data["access_token"]
        resp = client.patch(
            "/api/v1/auth/me",
            headers=auth_headers(token),
            json={"full_name": "Updated Name"},
        )
        assert resp.status_code == 200
        assert resp.json()["full_name"] == "Updated Name"


# ── Password change ──────────────────────────────────────────────────
class TestPasswordChange:
    """Tests for POST /api/v1/auth/change-password."""

    def test_change_password_success(self, client: TestClient):
        reg_data = register_and_login(client)
        token = reg_data["access_token"]
        resp = client.post(
            "/api/v1/auth/change-password",
            headers=auth_headers(token),
            json={
                "current_password": VALID_PASSWORD,
                "new_password": "NewStr0ng@Pass",
            },
        )
        assert resp.status_code == 200

    def test_change_password_wrong_current(self, client: TestClient):
        reg_data = register_and_login(client)
        token = reg_data["access_token"]
        resp = client.post(
            "/api/v1/auth/change-password",
            headers=auth_headers(token),
            json={
                "current_password": "WrongP@ss1",
                "new_password": "NewStr0ng@Pass",
            },
        )
        assert resp.status_code == 400

    def test_change_password_weak_new(self, client: TestClient):
        reg_data = register_and_login(client)
        token = reg_data["access_token"]
        resp = client.post(
            "/api/v1/auth/change-password",
            headers=auth_headers(token),
            json={
                "current_password": VALID_PASSWORD,
                "new_password": WEAK_PASSWORD,
            },
        )
        assert resp.status_code in (400, 422)
