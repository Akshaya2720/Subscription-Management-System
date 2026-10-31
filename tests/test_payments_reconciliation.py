import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
import pytest

from app.modules.customers.models import Customer
from app.modules.billing.models import Invoice, Payment, ReconciliationRun
from app.modules.billing.payments import PaymentService
from app.modules.billing.reconciliation import ReconciliationService


def test_payment_recording_allocations_and_refunds(client, db_session, org_a):
    """Test payment recording, multi-invoice partial allocations, and refund processing."""
    customer = Customer(
        id=uuid.uuid4(),
        organization_id=org_a.id,
        customer_code="CUST-PAY-01",
        contact_name="Zenith Finance",
        company_name="Zenith Dynamics",
        email="finance@zenith.org",
        status="ACTIVE",
    )
    db_session.add(customer)
    db_session.commit()

    # Create two invoices for customer
    inv1 = Invoice(
        id=uuid.uuid4(),
        organization_id=org_a.id,
        customer_id=customer.id,
        invoice_number="INV-PAY-001",
        issue_date=date.today(),
        due_date=date.today(),
        subtotal=Decimal("1000.00"),
        discount_total=Decimal("0.00"),
        tax_total=Decimal("0.00"),
        total_amount=Decimal("1000.00"),
        amount_paid=Decimal("0.00"),
        amount_due=Decimal("1000.00"),
        status="CONFIRMED",
        invoice_type="ONE_TIME",
        verification_status="VERIFIED",
    )
    inv2 = Invoice(
        id=uuid.uuid4(),
        organization_id=org_a.id,
        customer_id=customer.id,
        invoice_number="INV-PAY-002",
        issue_date=date.today(),
        due_date=date.today(),
        subtotal=Decimal("2000.00"),
        discount_total=Decimal("0.00"),
        tax_total=Decimal("0.00"),
        total_amount=Decimal("2000.00"),
        amount_paid=Decimal("0.00"),
        amount_due=Decimal("2000.00"),
        status="CONFIRMED",
        invoice_type="ONE_TIME",
        verification_status="VERIFIED",
    )
    db_session.add_all([inv1, inv2])
    db_session.commit()

    # 1. Record a single bulk payment of 1500 INR
    pay_resp = client.post(
        "/api/v1/payments",
        json={
            "customer_id": str(customer.id),
            "amount": "1500.00",
            "payment_method": "BANK_TRANSFER",
            "currency": "INR",
            "transaction_reference": "TXN-BANK-1500",
            "notes": "Bulk wire payment",
        },
    )
    assert pay_resp.status_code == 201
    pay_data = pay_resp.json()
    pay_id = pay_data["id"]

    # 2. Allocate 1000 to inv1 (fully paying inv1)
    alloc1_resp = client.post(
        f"/api/v1/payments/{pay_id}/allocate",
        json={"invoice_id": str(inv1.id), "amount": "1000.00"},
    )
    assert alloc1_resp.status_code == 200
    db_session.refresh(inv1)
    assert inv1.amount_paid == Decimal("1000.00")
    assert inv1.amount_due == Decimal("0.00")
    assert inv1.status == "PAID"

    # 3. Allocate remaining 500 to inv2 (partially paying inv2)
    alloc2_resp = client.post(
        f"/api/v1/payments/{pay_id}/allocate",
        json={"invoice_id": str(inv2.id), "amount": "500.00"},
    )
    assert alloc2_resp.status_code == 200
    db_session.refresh(inv2)
    assert inv2.amount_paid == Decimal("500.00")
    assert inv2.amount_due == Decimal("1500.00")
    assert inv2.status == "PARTIALLY_PAID"

    # 4. Attempt to allocate another 100 from this exhausted payment -> should fail
    alloc_fail_resp = client.post(
        f"/api/v1/payments/{pay_id}/allocate",
        json={"invoice_id": str(inv2.id), "amount": "100.00"},
    )
    assert alloc_fail_resp.status_code in [400, 422]
    assert "exceeds available payment balance" in alloc_fail_resp.json()["detail"]

    # 5. Process refund on a newly created payment
    pay2 = PaymentService.record_payment(
        db=db_session,
        organization_id=org_a.id,
        customer_id=customer.id,
        amount=Decimal("500.00"),
        payment_method="UPI",
    )
    # Partial refund of 200
    ref_resp = client.post(
        f"/api/v1/payments/{pay2.id}/refund",
        json={"amount": "200.00", "reason": "Customer overbilled on prior period"},
    )
    assert ref_resp.status_code == 200
    db_session.refresh(pay2)
    assert pay2.status == "PARTIALLY_REFUNDED"

    # Full refund of remaining 300
    client.post(
        f"/api/v1/payments/{pay2.id}/refund",
        json={"amount": "300.00", "reason": "Settlement of remaining balance"},
    )
    db_session.refresh(pay2)
    assert pay2.status == "REFUNDED"

    # Over-refund attempt should fail
    ref_fail_resp = client.post(
        f"/api/v1/payments/{pay2.id}/refund",
        json={"amount": "50.00", "reason": "Excess refund attempt"},
    )
    assert ref_fail_resp.status_code in [400, 422]


def test_reconciliation_csv_matching(client, db_session, org_a):
    """Test CSV bank statement parser, exact match, potential duplicate, amount mismatch, and review."""
    # 1. Setup payment record to match
    pay = PaymentService.record_payment(
        db=db_session,
        organization_id=org_a.id,
        customer_id=None,
        amount=Decimal("3450.00"),
        payment_method="BANK_TRANSFER",
        transaction_reference="ACH-REF-1001",
    )

    # 2. Build test CSV with:
    # Row 1: Exact match with ACH-REF-1001
    # Row 2 & 3: Duplicate references DUP-999
    # Row 4: Unmatched reference
    csv_data = (
        "transaction_date,reference,description,amount,currency\n"
        f"{date.today()},ACH-REF-1001,ACH Deposit Verisub settlement,3450.00,INR\n"
        f"{date.today()},DUP-999,Duplicate wire deposit batch A,500.00,INR\n"
        f"{date.today()},DUP-999,Duplicate wire deposit batch B,500.00,INR\n"
        f"{date.today()},UNKNOWN-REF-888,Check pending manual match,880.00,INR\n"
    )

    # Import via multipart upload
    files = {"file": ("bank_statement_nov.csv", csv_data, "text/csv")}
    resp = client.post("/api/v1/reconciliation/import", files=files)
    assert resp.status_code == 200
    run_data = resp.json()

    assert run_data["total_records"] == 4
    assert run_data["matched_count"] == 1  # ACH-REF-1001
    assert run_data["unmatched_count"] == 1  # UNKNOWN-REF-888
    assert run_data["discrepancy_count"] == 2  # The 2 duplicates

    # Review unmatched item
    unmatched_item = next(it for it in run_data["items"] if it["reference"] == "UNKNOWN-REF-888")
    review_resp = client.post(
        f"/api/v1/reconciliation/{unmatched_item['id']}/review",
        json={"decision": "MATCH", "notes": "Manually verified with branch manager"},
    )
    assert review_resp.status_code == 200
    assert review_resp.json()["match_status"] == "MATCHED"
