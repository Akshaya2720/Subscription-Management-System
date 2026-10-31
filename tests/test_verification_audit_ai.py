import uuid
from datetime import date, datetime, timezone, timedelta
from decimal import Decimal
import pytest

from app.modules.customers.models import Customer
from app.modules.plans.models import SubscriptionPlan
from app.modules.subscriptions.models import Subscription, SubscriptionItem
from app.modules.billing.models import (
    Contract,
    ServiceCommitment,
    ServiceEvent,
    Invoice,
    AuditEvent,
)
from app.modules.billing.verification import VerificationService
from app.modules.billing.anomaly import AnomalyDetectionService
from app.modules.billing.audit import AuditService, GENESIS_HASH


def test_contract_verification_and_credit_approval(client, db_session, org_a):
    """Test SLA contract commitments vs service events, breach detection, and credit approval."""
    # 1. Setup subscription
    customer = Customer(
        id=uuid.uuid4(),
        organization_id=org_a.id,
        customer_code="CUST-VERIF-01",
        contact_name="Mission Critical Support",
        company_name="Mission Critical Systems",
        email="sla@critical.com",
        status="ACTIVE",
    )
    plan = SubscriptionPlan(
        id=uuid.uuid4(),
        organization_id=org_a.id,
        name="Mission Critical 99.9% Plan",
        billing_frequency="MONTHLY",
        plan_price=Decimal("50000.00"),
        status="ACTIVE",
    )
    sub = Subscription(
        id=uuid.uuid4(),
        organization_id=org_a.id,
        customer_id=customer.id,
        plan_id=plan.id,
        subscription_number="SUB-CRITICAL-01",
        start_date=date.today() - timedelta(days=30),
        next_billing_date=date.today(),
        billing_frequency="MONTHLY",
        status="ACTIVE",
        currency="INR",
    )
    db_session.add_all([customer, plan, sub])
    db_session.commit()

    # 2. Create Contract with Uptime SLA commitment (99.9% target, 500 penalty per 0.1% breach)
    contract_resp = client.post(
        "/api/v1/verification/contracts",
        json={
            "subscription_id": str(sub.id),
            "contract_reference": "CTR-CRITICAL-2026",
            "start_date": str(date.today() - timedelta(days=30)),
            "commitments": [
                {
                    "commitment_type": "UPTIME",
                    "expected_value": "99.9000",
                    "measurement_unit": "PERCENTAGE",
                    "verification_rule": "GREATER_OR_EQUAL",
                    "penalty_rate_per_unit": "500.00",
                }
            ],
        },
    )
    assert contract_resp.status_code == 201

    # 3. Ingest actual service delivery event showing outage (actual uptime 98.40%)
    event_resp = client.post(
        "/api/v1/verification/events",
        json={
            "subscription_id": str(sub.id),
            "event_type": "UPTIME",
            "actual_value": "98.4000",
            "event_timestamp": datetime.now(timezone.utc).isoformat(),
            "evidence_reference": "Datadog Incident #INC-44019 (Outage 1h 9m)",
            "source": "MONITORING_SYSTEM",
            "status": "VERIFIED",
        },
    )
    assert event_resp.status_code == 201

    # 4. Run Contract-to-Bill Value Verification
    run_resp = client.post(f"/api/v1/verification/run/{sub.id}")
    assert run_resp.status_code == 200
    run_data = run_resp.json()
    assert run_data["overall_result"] == "BREACH"
    assert len(run_data["results"]) == 1

    result = run_data["results"][0]
    assert result["result"] == "FAIL"
    assert "SLA Breach" in result["explanation"]
    assert "INC-44019" in result["evidence_reference"]
    assert len(result["service_credits"]) == 1

    credit = result["service_credits"][0]
    assert credit["status"] == "PROPOSED"
    assert Decimal(str(credit["proposed_credit"])) > Decimal("0.00")

    # 5. Approve the service credit
    credit_id = credit["id"]
    approve_resp = client.post(
        f"/api/v1/verification/credits/{credit_id}/approve",
        json={"notes": "Outage confirmed by engineering; customer credit authorized."},
    )
    assert approve_resp.status_code == 200
    assert approve_resp.json()["status"] == "APPROVED"
    assert approve_resp.json()["approved_credit"] == credit["proposed_credit"]


def test_ai_anomaly_detection_and_assistant(client, db_session, org_a):
    """Test deterministic explainable anomaly detection and controlled business assistant."""
    customer = Customer(
        id=uuid.uuid4(),
        organization_id=org_a.id,
        customer_code="CUST-AI-01",
        contact_name="Nova Ops",
        company_name="Nova Technologies",
        email="ops@novatech.ai",
        status="ACTIVE",
    )
    db_session.add(customer)
    db_session.commit()

    # Create an invoice with excessive discount (> 50%) and overdue date
    inv = Invoice(
        id=uuid.uuid4(),
        organization_id=org_a.id,
        customer_id=customer.id,
        invoice_number="INV-AI-TEST-001",
        issue_date=date.today() - timedelta(days=10),
        due_date=date.today() - timedelta(days=5),  # Overdue
        subtotal=Decimal("10000.00"),
        discount_total=Decimal("7000.00"),  # 70% discount
        tax_total=Decimal("0.00"),
        total_amount=Decimal("3000.00"),
        amount_paid=Decimal("0.00"),
        amount_due=Decimal("3000.00"),
        status="CONFIRMED",
        invoice_type="ONE_TIME",
        verification_status="VERIFIED",
    )
    db_session.add(inv)
    db_session.commit()

    # 1. Run Anomaly Detection
    anom_resp = client.post(f"/api/v1/ai/anomalies/detect?invoice_id={inv.id}")
    assert anom_resp.status_code == 200
    anomalies = anom_resp.json()
    assert len(anomalies) >= 1
    disc_anom = next(a for a in anomalies if a["anomaly_type"] == "UNUSUAL_DISCOUNT")
    assert disc_anom["severity"] == "MEDIUM"
    assert "exceeds 50% of invoice subtotal" in disc_anom["explanation"]

    # 2. Query Business Assistant for outstanding & overdue invoices
    q_overdue = client.post(
        "/api/v1/ai/assistant/query",
        json={"prompt": "Which invoices are overdue?"},
    )
    assert q_overdue.status_code == 200
    res_data = q_overdue.json()
    assert res_data["category"] == "OVERDUE_INVOICES"
    assert "INV-AI-TEST-001" in res_data["answer"]

    q_outstanding = client.post(
        "/api/v1/ai/assistant/query",
        json={"prompt": "What is our total outstanding amount?"},
    )
    assert q_outstanding.status_code == 200
    assert "3,000.00 INR" in q_outstanding.json()["answer"]


def test_tamper_evident_audit_and_blockchain(client, db_session, org_a):
    """Test cryptographic SHA-256 hash chaining, verification, tampering detection, and testnet anchoring."""
    # 1. Generate 3 audit events
    ev1 = AuditService.record_audit_event(
        db_session, org_a.id, "INVOICE_CREATED", "INVOICE", uuid.uuid4(), "Created invoice INV-001"
    )
    ev2 = AuditService.record_audit_event(
        db_session, org_a.id, "PAYMENT_RECEIVED", "PAYMENT", uuid.uuid4(), "Recorded payment of 1000 INR"
    )
    ev3 = AuditService.record_audit_event(
        db_session, org_a.id, "CREDIT_APPROVED", "SERVICE_CREDIT", uuid.uuid4(), "Approved SLA credit"
    )

    # 2. Check hash chain links
    assert ev1.previous_hash == GENESIS_HASH
    assert ev2.previous_hash == ev1.current_hash
    assert ev3.previous_hash == ev2.current_hash

    # 3. Verify integrity via API
    verify_resp = client.get("/api/v1/audit/verify")
    assert verify_resp.status_code == 200
    assert verify_resp.json()["is_valid"] is True
    assert verify_resp.json()["total_blocks_checked"] >= 3

    # 4. Anchor to blockchain testnet
    anchor_resp = client.post(
        "/api/v1/audit/anchor",
        json={"network": "Ethereum Sepolia Testnet"},
    )
    assert anchor_resp.status_code == 200
    anchor_data = anchor_resp.json()
    assert anchor_data["anchored"] is True
    assert anchor_data["tx_hash"].startswith("0x")
    assert anchor_data["network"] == "Ethereum Sepolia Testnet"

    # 5. Tamper with a block and verify tamper detection
    ev2.change_summary = "TAMPERED: Altered payment amount secretly"
    db_session.commit()

    tamper_verify = AuditService.verify_hash_chain(db_session, org_a.id)
    assert tamper_verify["is_valid"] is False
    assert "mismatch" in tamper_verify["details"].lower() or "broken" in tamper_verify["details"].lower()


def test_organization_isolation_in_billing(db_session, org_a, org_b):
    """Ensure Organization B cannot see or manipulate Organization A's invoices, payments, or contracts."""
    from fastapi.testclient import TestClient
    from app.core.database import get_db
    from app.core.auth import get_current_organization
    from app.main import app

    def get_db_override():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = get_db_override

    # Create invoice in Org A
    cust_a = Customer(
        id=uuid.uuid4(),
        organization_id=org_a.id,
        customer_code="CUST-ISO-A",
        contact_name="Tenant A Contact",
        company_name="Tenant A Customer",
        email="tenant_a@iso.com",
        status="ACTIVE",
    )
    db_session.add(cust_a)
    db_session.commit()

    inv_a = Invoice(
        id=uuid.uuid4(),
        organization_id=org_a.id,
        customer_id=cust_a.id,
        invoice_number="INV-TENANT-A-01",
        issue_date=date.today(),
        due_date=date.today(),
        subtotal=Decimal("1000.00"),
        total_amount=Decimal("1000.00"),
        amount_paid=Decimal("0.00"),
        amount_due=Decimal("1000.00"),
        status="DRAFT",
    )
    db_session.add(inv_a)
    db_session.commit()

    # Query with Org A context -> returns invoice
    app.dependency_overrides[get_current_organization] = lambda: org_a
    with TestClient(app) as client_a:
        resp_a = client_a.get("/api/v1/invoices")
        assert resp_a.status_code == 200
        inv_ids_a = [i["id"] for i in resp_a.json()]
        assert str(inv_a.id) in inv_ids_a

    # Query with Org B context -> MUST NOT return Org A invoice
    app.dependency_overrides[get_current_organization] = lambda: org_b
    with TestClient(app) as client_b:
        resp_b = client_b.get("/api/v1/invoices")
        assert resp_b.status_code == 200
        inv_ids_b = [i["id"] for i in resp_b.json()]
        assert str(inv_a.id) not in inv_ids_b

        # Direct access to Org A invoice ID by Org B returns 404
        resp_b_direct = client_b.get(f"/api/v1/invoices/{inv_a.id}")
        assert resp_b_direct.status_code == 404
