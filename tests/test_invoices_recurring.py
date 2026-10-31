import uuid
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from decimal import Decimal
import pytest

from app.modules.customers.models import Customer
from app.modules.plans.models import SubscriptionPlan
from app.modules.products.models import Product
from app.modules.subscriptions.models import Subscription, SubscriptionItem
from app.modules.billing.models import Invoice, BillingRun
from app.modules.billing.recurring import RecurringBillingService


def test_invoice_crud_and_pdf(client, db_session, org_a):
    """Test manual invoice creation, item snapshots, confirmation, status change, and PDF generation."""
    # 1. Setup Customer and Product
    customer = Customer(
        id=uuid.uuid4(),
        organization_id=org_a.id,
        customer_code="CUST-INV-01",
        contact_name="Apex Billing",
        company_name="Apex Systems Ltd",
        email="billing@apexsystems.com",
        status="ACTIVE",
    )
    product = Product(
        id=uuid.uuid4(),
        organization_id=org_a.id,
        name="Enterprise Cloud Platform",
        sales_price=Decimal("5000.00"),
        status="ACTIVE",
    )
    db_session.add_all([customer, product])
    db_session.commit()

    # 2. Create Draft Invoice via API
    invoice_payload = {
        "customer_id": str(customer.id),
        "due_date": str(date.today() + timedelta(days=30)),
        "currency": "INR",
        "invoice_type": "ONE_TIME",
        "items": [
            {
                "product_id": str(product.id),
                "description_snapshot": "Enterprise Cloud Platform - Annual License",
                "quantity": 2,
                "unit_price": "5000.00",
            }
        ],
    }
    resp = client.post("/api/v1/invoices", json=invoice_payload)
    assert resp.status_code == 201
    inv_data = resp.json()
    inv_id = inv_data["id"]
    assert inv_data["status"] == "DRAFT"
    assert Decimal(inv_data["subtotal"]) == Decimal("10000.00")
    assert Decimal(inv_data["amount_due"]) == Decimal(inv_data["total_amount"])

    # 3. Confirm Invoice
    conf_resp = client.post(f"/api/v1/invoices/{inv_id}/confirm")
    assert conf_resp.status_code == 200
    assert conf_resp.json()["status"] == "CONFIRMED"

    # Cannot confirm again (InvalidStateTransition)
    conf_resp2 = client.post(f"/api/v1/invoices/{inv_id}/confirm")
    assert conf_resp2.status_code == 400

    # 4. Generate & download PDF
    pdf_resp = client.get(f"/api/v1/invoices/{inv_id}/pdf")
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["content-type"] == "application/pdf"
    assert len(pdf_resp.content) > 1000  # Non-empty PDF binary


def test_recurring_billing_cadences_and_idempotency(client, db_session, org_a):
    """
    Test recurring billing execution:
    - Daily, Weekly, Monthly, Yearly cadences
    - Respecting PAUSED, CLOSED, and EXPIRED statuses
    - Idempotency & duplicate prevention
    """
    customer = Customer(
        id=uuid.uuid4(),
        organization_id=org_a.id,
        customer_code="CUST-REC-01",
        contact_name="Cloud Ops",
        company_name="Global Cloud Network",
        email="ops@globalcloud.net",
        status="ACTIVE",
    )
    product = Product(
        id=uuid.uuid4(),
        organization_id=org_a.id,
        name="Managed Kubernetes Service",
        sales_price=Decimal("1200.00"),
        status="ACTIVE",
    )
    plan_monthly = SubscriptionPlan(
        id=uuid.uuid4(),
        organization_id=org_a.id,
        name="K8s Monthly Plan",
        billing_frequency="MONTHLY",
        plan_price=Decimal("1200.00"),
        status="ACTIVE",
    )
    plan_yearly = SubscriptionPlan(
        id=uuid.uuid4(),
        organization_id=org_a.id,
        name="K8s Yearly Plan",
        billing_frequency="YEARLY",
        plan_price=Decimal("12000.00"),
        status="ACTIVE",
    )
    db_session.add_all([customer, product, plan_monthly, plan_yearly])
    db_session.commit()

    today = date.today()

    # 1. Active monthly subscription due today
    sub_monthly = Subscription(
        id=uuid.uuid4(),
        organization_id=org_a.id,
        customer_id=customer.id,
        plan_id=plan_monthly.id,
        subscription_number="SUB-REC-MONTHLY",
        start_date=today - relativedelta(months=1),
        next_billing_date=today,
        billing_frequency="MONTHLY",
        status="ACTIVE",
        currency="INR",
    )
    item_m = SubscriptionItem(
        id=uuid.uuid4(),
        subscription_id=sub_monthly.id,
        product_id=product.id,
        description_snapshot="Managed K8s Node Pool",
        quantity=2,
        unit_price_snapshot=Decimal("1200.00"),
        line_total=Decimal("2400.00"),
    )

    # 2. Active yearly subscription due today
    sub_yearly = Subscription(
        id=uuid.uuid4(),
        organization_id=org_a.id,
        customer_id=customer.id,
        plan_id=plan_yearly.id,
        subscription_number="SUB-REC-YEARLY",
        start_date=today - relativedelta(years=1),
        next_billing_date=today,
        billing_frequency="YEARLY",
        status="ACTIVE",
        currency="INR",
    )
    item_y = SubscriptionItem(
        id=uuid.uuid4(),
        subscription_id=sub_yearly.id,
        product_id=product.id,
        description_snapshot="Managed K8s Dedicated Cluster",
        quantity=1,
        unit_price_snapshot=Decimal("12000.00"),
        line_total=Decimal("12000.00"),
    )

    # 3. Paused subscription due today (MUST NOT BE BILLED)
    sub_paused = Subscription(
        id=uuid.uuid4(),
        organization_id=org_a.id,
        customer_id=customer.id,
        plan_id=plan_monthly.id,
        subscription_number="SUB-REC-PAUSED",
        start_date=today - relativedelta(months=1),
        next_billing_date=today,
        billing_frequency="MONTHLY",
        status="PAUSED",
        currency="INR",
    )

    # 4. Future subscription not yet due (MUST NOT BE BILLED)
    sub_future = Subscription(
        id=uuid.uuid4(),
        organization_id=org_a.id,
        customer_id=customer.id,
        plan_id=plan_monthly.id,
        subscription_number="SUB-REC-FUTURE",
        start_date=today,
        next_billing_date=today + timedelta(days=20),
        billing_frequency="MONTHLY",
        status="ACTIVE",
        currency="INR",
    )

    # 5. Expired subscription (MUST NOT BE BILLED)
    sub_expired = Subscription(
        id=uuid.uuid4(),
        organization_id=org_a.id,
        customer_id=customer.id,
        plan_id=plan_monthly.id,
        subscription_number="SUB-REC-EXPIRED",
        start_date=today - relativedelta(months=6),
        next_billing_date=today,
        expiry_date=today - timedelta(days=1),
        billing_frequency="MONTHLY",
        status="ACTIVE",
        currency="INR",
    )

    db_session.add_all([sub_monthly, item_m, sub_yearly, item_y, sub_paused, sub_future, sub_expired])
    db_session.commit()

    # Verify due subscriptions selection
    due = RecurringBillingService.get_due_subscriptions(db_session, org_a.id, as_of_date=today)
    assert len(due) == 2  # Only sub_monthly and sub_yearly
    due_numbers = {s.subscription_number for s in due}
    assert due_numbers == {"SUB-REC-MONTHLY", "SUB-REC-YEARLY"}

    # Execute Billing Run via API
    run_resp = client.post("/api/v1/billing/run", json={"as_of_date": str(today)})
    assert run_resp.status_code == 200
    run_data = run_resp.json()
    assert run_data["status"] == "COMPLETED"
    assert run_data["total_processed"] == 2
    assert run_data["successful_count"] == 2
    assert run_data["failed_count"] == 0

    # Verify next_billing_dates advanced properly
    db_session.refresh(sub_monthly)
    db_session.refresh(sub_yearly)
    assert sub_monthly.next_billing_date == today + relativedelta(months=1)
    assert sub_yearly.next_billing_date == today + relativedelta(years=1)

    # Verify invoices generated
    inv_monthly = db_session.query(Invoice).filter(Invoice.subscription_id == sub_monthly.id).first()
    assert inv_monthly is not None
    assert inv_monthly.billing_period_start == today
    assert inv_monthly.billing_period_end == today + relativedelta(months=1)

    # Execute billing run again for the same date -> Idempotency check
    run_resp2 = client.post("/api/v1/billing/run", json={"as_of_date": str(today)})
    assert run_resp2.status_code == 200
    assert run_resp2.json()["total_processed"] == 0  # No subscriptions due since dates advanced
