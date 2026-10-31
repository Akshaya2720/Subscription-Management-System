"""Comprehensive test suite for Phase 2 Backend features:
- Auth & RBAC (Argon2id, Password Policy, Token Refresh, Reset, Roles)
- Billing, Taxes, Discounts & Idempotent Recurring Billing
- Simulated Payment Gateway & Receipt Generation
- Deterministic SLA Contract-to-Bill Verification & Tamper-Evident SHA-256 Audit Trail
"""

import uuid
from decimal import Decimal
from datetime import date, timedelta
import pytest
from fastapi.testclient import TestClient

from app.models.billing import InvoiceStatus, PaymentMethod, DiscountType
from app.models.auth import UserRole


# ── 1. Auth, Password Policy & RBAC Tests ────────────────────────────────────

def test_auth_registration_and_password_policy(client: TestClient):
    # Test weak password rejection (no special character)
    weak_payload = {
        "organization_name": "Acme Corp",
        "organization_email": "org@acme.com",
        "admin_name": "Alice Admin",
        "admin_email": "alice@acme.com",
        "admin_password": "WeakPassword123",  # no special char
    }
    resp_weak = client.post("/api/v1/auth/register", json=weak_payload)
    assert resp_weak.status_code == 400
    assert "special character" in resp_weak.json()["detail"]

    # Test valid registration
    valid_payload = {
        "organization_name": "Acme Corp",
        "organization_email": "org@acme.com",
        "admin_name": "Alice Admin",
        "admin_email": "alice@acme.com",
        "admin_password": "Str0ng!AdminPass",
    }
    resp = client.post("/api/v1/auth/register", json=valid_payload)
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["email"] == "alice@acme.com"
    assert data["user"]["role"] == "ADMIN"

    # Test duplicate registration rejection
    resp_dup = client.post("/api/v1/auth/register", json=valid_payload)
    assert resp_dup.status_code == 409


def test_auth_login_refresh_and_logout(client: TestClient):
    # Register first
    client.post(
        "/api/v1/auth/register",
        json={
            "organization_name": "Login Test Org",
            "organization_email": "org@logintest.com",
            "admin_name": "Login Admin",
            "admin_email": "login_admin@test.com",
            "admin_password": "Str0ng!AdminPass",
        },
    )

    # 1. Login
    login_payload = {
        "email": "login_admin@test.com",
        "password": "Str0ng!AdminPass",
    }
    resp_login = client.post("/api/v1/auth/login", json=login_payload)
    assert resp_login.status_code == 200
    tokens = resp_login.json()
    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]

    # 2. Token refresh
    resp_refresh = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert resp_refresh.status_code == 200
    assert "access_token" in resp_refresh.json()

    # 3. Logout (revokes refresh token)
    resp_logout = client.post("/api/v1/auth/logout", json={"refresh_token": refresh_token})
    assert resp_logout.status_code == 200

    # 4. Refresh with revoked token should fail
    resp_revoked = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert resp_revoked.status_code == 401


def test_password_reset_flow(client: TestClient):
    # Register user
    client.post(
        "/api/v1/auth/register",
        json={
            "organization_name": "Reset Test Org",
            "organization_email": "org@resettest.com",
            "admin_name": "Reset Admin",
            "admin_email": "reset_admin@test.com",
            "admin_password": "Str0ng!AdminPass",
        },
    )

    # Request reset token
    forgot_resp = client.post("/api/v1/auth/forgot-password", json={"email": "reset_admin@test.com"})
    assert forgot_resp.status_code == 200
    reset_token = forgot_resp.json().get("reset_token")
    assert reset_token is not None

    # Perform reset
    new_pass = "Br@ndNewStr0ngP@ss"
    reset_resp = client.post(
        "/api/v1/auth/reset-password",
        json={"token": reset_token, "new_password": new_pass},
    )
    assert reset_resp.status_code == 200

    # Login with new password
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "reset_admin@test.com", "password": new_pass},
    )
    assert login_resp.status_code == 200


def test_rbac_admin_creates_staff_and_staff_restrictions(client: TestClient):
    # Register admin
    reg_resp = client.post(
        "/api/v1/auth/register",
        json={
            "organization_name": "RBAC Org",
            "organization_email": "org@rbac.com",
            "admin_name": "RBAC Admin",
            "admin_email": "rbac_admin@test.com",
            "admin_password": "Str0ng!AdminPass",
        },
    )
    admin_token = reg_resp.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Admin creates staff
    staff_payload = {
        "full_name": "Bob Staff",
        "email": "bob@rbac.com",
        "password": "St@ffPassword123!",
    }
    resp_staff = client.post("/api/v1/users/staff", json=staff_payload, headers=admin_headers)
    assert resp_staff.status_code == 201
    assert resp_staff.json()["role"] == "STAFF"

    # Login as Bob (STAFF)
    staff_login = client.post(
        "/api/v1/auth/login",
        json={"email": "bob@rbac.com", "password": "St@ffPassword123!"},
    )
    staff_token = staff_login.json()["access_token"]
    staff_headers = {"Authorization": f"Bearer {staff_token}"}

    # Staff attempts to create another staff -> FORBIDDEN (403)
    resp_forbidden = client.post(
        "/api/v1/users/staff",
        json={"full_name": "Charlie", "email": "charlie@rbac.com", "password": "Ch@rliePass123!"},
        headers=staff_headers,
    )
    assert resp_forbidden.status_code == 403


# ── 2. Tax, Discount & Automated Billing Engine Tests ─────────────────────────

def test_tax_and_discount_engines(client: TestClient):
    # 1. Create Tax Rule (ADMIN only)
    tax_payload = {
        "name": "Standard VAT",
        "tax_code": "VAT-10",
        "rate_percent": "10.00",
        "country": "US",
        "is_default": True,
        "is_active": True,
    }
    resp_tax = client.post("/api/v1/taxes", json=tax_payload)
    assert resp_tax.status_code == 201
    assert Decimal(resp_tax.json()["rate_percent"]) == Decimal("10.00")

    # 2. Create Discount (ADMIN only)
    disc_payload = {
        "code": "SUMMER20",
        "description": "20% Summer Launch Discount",
        "discount_type": "PERCENTAGE",
        "amount": "20.00",
        "min_purchase_amount": "50.00",
        "min_quantity": 1,
        "max_uses": 2,
        "is_active": True,
    }
    resp_disc = client.post("/api/v1/discounts", json=disc_payload)
    assert resp_disc.status_code == 201
    assert resp_disc.json()["code"] == "SUMMER20"


def test_idempotent_recurring_billing_run(client: TestClient):
    # Create customer
    cust_resp = client.post(
        "/api/v1/customers",
        json={
            "customer_code": "CUST-BILL-01",
            "company_name": "Billing Corp",
            "contact_name": "David Miller",
            "email": "david@billingcorp.com",
            "status": "ACTIVE",
        },
    )
    cust_id = cust_resp.json()["id"]

    # Create product
    prod_resp = client.post(
        "/api/v1/products",
        json={
            "name": "Cloud VM 4-Core",
            "sales_price": "100.00",
            "cost_price": "50.00",
        },
    )
    prod_id = prod_resp.json()["id"]

    # Create plan
    plan_resp = client.post(
        "/api/v1/plans",
        json={
            "name": "Cloud Host Pro",
            "billing_frequency": "MONTHLY",
            "plan_price": "100.00",
            "minimum_quantity": 1,
            "status": "ACTIVE",
        },
    )
    plan_id = plan_resp.json()["id"]

    # Create active subscription due today
    today = date.today()
    sub_resp = client.post(
        "/api/v1/subscriptions",
        json={
            "customer_id": cust_id,
            "plan_id": plan_id,
            "start_date": str(today - timedelta(days=30)),
            "billing_frequency": "MONTHLY",
            "items": [
                {
                    "product_id": prod_id,
                    "description_snapshot": "Cloud VM 4-Core",
                    "quantity": 1,
                    "unit_price_snapshot": "100.00",
                }
            ],
        },
    )
    assert sub_resp.status_code == 201
    sub_id = sub_resp.json()["id"]
    # Activate subscription
    act_resp = client.post(f"/api/v1/subscriptions/{sub_id}/activate")
    assert act_resp.status_code == 200
    billing_date = act_resp.json()["next_billing_date"]

    # 1. Trigger recurring billing run
    run_resp = client.post("/api/v1/invoices/recurring-run", json={"run_date": billing_date, "auto_confirm": True})
    assert run_resp.status_code == 200
    run_data = run_resp.json()
    assert run_data["invoices_created"] >= 1
    assert run_data["invoices_skipped"] == 0

    # 2. Trigger SECOND recurring billing run -> MUST BE IDEMPOTENT (no duplicate invoice created)
    second_run = client.post("/api/v1/invoices/recurring-run", json={"run_date": billing_date, "auto_confirm": True})
    assert second_run.status_code == 200
    second_data = second_run.json()
    # No duplicate invoice should be created!
    assert second_data["invoices_created"] == 0


# ── 3. Simulated Payment Gateway Tests ────────────────────────────────────────

def test_simulated_payment_gateway(client: TestClient):
    # Setup customer and confirmed invoice
    cust_resp = client.post(
        "/api/v1/customers",
        json={
            "customer_code": "CUST-PAY-01",
            "company_name": "Payment Test Co",
            "contact_name": "Pay Tester",
            "email": "pay@test.com",
            "status": "ACTIVE",
        },
    )
    cust_id = cust_resp.json()["id"]

    inv_resp = client.post(
        "/api/v1/invoices",
        json={
            "customer_id": cust_id,
            "due_date": str(date.today() + timedelta(days=14)),
            "items": [
                {
                    "description": "SaaS Platform License",
                    "quantity": 1,
                    "unit_price": "250.00",
                    "tax_percent": "0.00",
                }
            ],
        },
    )
    assert inv_resp.status_code == 201
    inv_id = inv_resp.json()["id"]

    # Confirm invoice
    confirm_resp = client.post(f"/api/v1/invoices/{inv_id}/confirm")
    assert confirm_resp.status_code == 200
    assert confirm_resp.json()["status"] == "CONFIRMED"

    # Test overpayment rejection (> 250.00)
    overpay_resp = client.post(
        f"/api/v1/invoices/{inv_id}/payments",
        json={"amount": "300.00", "payment_method": "SIMULATED"},
    )
    assert overpay_resp.status_code == 422
    assert "exceeds" in overpay_resp.json()["detail"].lower()

    # Record full payment
    pay_resp = client.post(
        f"/api/v1/invoices/{inv_id}/payments",
        json={
            "amount": "250.00",
            "payment_method": "SIMULATED",
            "reference": "TEST-CARD-4242",
            "notes": "Automated payment simulation",
        },
    )
    assert pay_resp.status_code == 200
    receipt = pay_resp.json()
    assert receipt["status"] == "SUCCESS"
    assert Decimal(str(receipt["remaining_balance"])) == Decimal("0.00")

    # Verify invoice status transitioned to PAID
    inv_updated = client.get(f"/api/v1/invoices/{inv_id}").json()
    assert inv_updated["status"] == "PAID"
    assert Decimal(str(inv_updated["amount_paid"])) == Decimal("250.00")
    assert Decimal(str(inv_updated["amount_due"])) == Decimal("0.00")


# ── 4. Deterministic SLA Telemetry & SHA-256 Audit Trail Tests ────────────────

def test_sla_verification_contract_and_breach_credit(client: TestClient):
    # Setup customer, plan, subscription
    cust_resp = client.post(
        "/api/v1/customers",
        json={
            "customer_code": "CUST-SLA-01",
            "company_name": "SLA Test Co",
            "contact_name": "SLA Lead",
            "email": "sla@test.com",
            "status": "ACTIVE",
        },
    )
    cust_id = cust_resp.json()["id"]

    plan_resp = client.post(
        "/api/v1/plans",
        json={
            "name": "SLA High Tier Plan",
            "billing_frequency": "MONTHLY",
            "plan_price": "500.00",
            "minimum_quantity": 1,
            "status": "ACTIVE",
        },
    )
    plan_id = plan_resp.json()["id"]

    # Create product for subscription
    prod_resp = client.post(
        "/api/v1/products",
        json={
            "name": f"SLA Cloud Product-{uuid.uuid4().hex[:6]}",
            "sales_price": "500.00",
            "cost_price": "200.00",
        },
    )
    prod_id = prod_resp.json()["id"]

    sub_resp = client.post(
        "/api/v1/subscriptions",
        json={
            "customer_id": cust_id,
            "plan_id": plan_id,
            "start_date": str(date.today()),
            "billing_frequency": "MONTHLY",
            "items": [
                {
                    "product_id": prod_id,
                    "description_snapshot": "SLA Cloud VM",
                    "quantity": 1,
                    "unit_price_snapshot": "500.00",
                }
            ],
        },
    )
    assert sub_resp.status_code == 201
    sub_id = sub_resp.json()["id"]

    # Register SLA contract
    contract_payload = {
        "contract_number": f"SLA-GOLD-{uuid.uuid4().hex[:6].upper()}",
        "subscription_id": sub_id,
        "service_name": "High Availability Cloud Cluster",
        "sla_commitment_description": "Guaranteed 99.99% monthly uptime",
        "target_uptime_percentage": "99.99",
        "actual_recorded_telemetry": "Telemetry active",
        "proposed_credit_amount": "0.00",
    }
    resp_contract = client.post("/api/v1/verification/contracts", json=contract_payload)
    assert resp_contract.status_code == 201
    contract_id = resp_contract.json()["id"]

    # Run SLA telemetry evaluation with breach (98.50% measured vs 99.99% target)
    eval_resp = client.post(
        "/api/v1/verification/contracts/evaluate",
        json={
            "contract_id": contract_id,
            "measured_uptime_percentage": "98.50",
            "telemetry_window": "October 2026",
        },
    )
    assert eval_resp.status_code == 200
    result = eval_resp.json()
    assert result["breach_detected"] is True
    assert Decimal(str(result["outage_shortfall_percent"])) == Decimal("1.49")
    assert Decimal(str(result["proposed_credit_amount"])) > Decimal("0.00")
    assert result["adjudication_status"] == "CREDIT_APPROVED"


def test_sha256_audit_trail_and_cryptographic_verification(client: TestClient, db_session, org_a):
    from app.modules.verification.service import AuditService

    audit_service = AuditService(db_session)
    audit_service.log_action(
        org_id=org_a.id,
        entity_type="INVOICE",
        entity_id="INV-001",
        action="SETTLE",
        actor_email="finance@acme.com",
        payload={"amount": 110.0, "status": "PAID"},
    )
    audit_service.log_action(
        org_id=org_a.id,
        entity_type="SUBSCRIPTION",
        entity_id="SUB-001",
        action="RENEW",
        actor_email="system@verisub.local",
        payload={"cycle": 2},
    )

    # Verify audit chain via API endpoint
    verify_resp = client.get("/api/v1/audit/verify", headers={"X-Organization-Id": str(org_a.id)})
    assert verify_resp.status_code == 200
    chain_result = verify_resp.json()
    assert chain_result["is_valid"] is True
    assert chain_result["total_blocks_verified"] >= 2
    assert chain_result["tampered_block_sequence"] is None
