from decimal import Decimal
from datetime import date, datetime, timezone
import uuid
from app.modules.billing.models import Invoice, Payment


def test_digital_twin_accuracy(client, db_session, org_a):
    # 1. Setup Customer
    cust_resp = client.post(
        "/api/v1/customers",
        json={
            "customer_code": "CUST-TWIN-01",
            "company_name": "Digital Twin Enterprises",
            "contact_name": "Meera Krishnan",
            "email": "meera@twinent.com",
            "phone": "+91 9123456789",
            "billing_address": "Tidel Park, Chennai, Tamil Nadu",
            "tax_identifier": "33AAACD1234F1Z5",
            "status": "ACTIVE",
        },
    )
    cust_id = cust_resp.json()["id"]

    # 2. Setup Plan
    plan_resp = client.post(
        "/api/v1/plans",
        json={
            "name": "Omnichannel Suite Plan",
            "billing_frequency": "MONTHLY",
            "plan_price": "7500.00",
            "status": "ACTIVE",
        },
    )
    plan_id = plan_resp.json()["id"]

    # 3. Setup Product & Variant
    prod_resp = client.post(
        "/api/v1/products",
        json={
            "name": "Helpdesk Bot",
            "product_type": "SAAS",
            "sales_price": "3000.00",
            "status": "ACTIVE",
            "variants": [
                {
                    "variant_name": "Multilingual AI",
                    "additional_price": "1200.00",
                    "status": "ACTIVE",
                }
            ],
        },
    )
    prod_data = prod_resp.json()
    prod_id = prod_data["id"]
    var_id = prod_data["variants"][0]["id"]

    # 4. Create Quotation & Confirm
    q_resp = client.post(
        "/api/v1/quotations",
        json={
            "customer_id": cust_id,
            "expiry_date": str(date.today()),
            "items": [
                {
                    "product_id": prod_id,
                    "variant_id": var_id,
                    "plan_id": plan_id,
                    "quantity": 2,
                    "tax_configuration_reference": "GST_18",
                }
            ],
        },
    )
    q_id = q_resp.json()["id"]
    client.post(f"/api/v1/quotations/{q_id}/confirm")

    # 5. Convert to Subscription & Activate
    conv_resp = client.post(f"/api/v1/quotations/{q_id}/convert-to-subscription")
    sub_id = conv_resp.json()["subscription_id"]
    client.post(f"/api/v1/subscriptions/{sub_id}/activate")

    # 6. Insert actual Invoice and Payment records into database
    invoice = Invoice(
        id=uuid.uuid4(),
        organization_id=org_a.id,
        customer_id=uuid.UUID(cust_id),
        subscription_id=uuid.UUID(sub_id),
        invoice_number="INV-2026-TWIN-001",
        issue_date=date.today(),
        due_date=date.today(),
        subtotal=Decimal("8400.00"),
        discount_total=Decimal("0.00"),
        tax_total=Decimal("1512.00"),
        total_amount=Decimal("9912.00"),
        status="PAID",
        verification_status="VERIFIED",
    )
    db_session.add(invoice)
    db_session.flush()

    payment = Payment(
        id=uuid.uuid4(),
        organization_id=org_a.id,
        invoice_id=invoice.id,
        amount=Decimal("9912.00"),
        payment_method="UPI_AUTOPAY",
        transaction_reference="UPI/20261031/TXN987654",
        status="COMPLETED",
    )
    db_session.add(payment)
    db_session.commit()

    # 7. Query Subscription Digital Twin
    twin_resp = client.get(f"/api/v1/subscriptions/{sub_id}/digital-twin")
    assert twin_resp.status_code == 200
    twin = twin_resp.json()

    # Verify Customer
    assert twin["customer"]["customer_code"] == "CUST-TWIN-01"
    assert twin["customer"]["email"] == "meera@twinent.com"
    assert twin["customer"]["tax_identifier"] == "33AAACD1234F1Z5"

    # Verify Plan
    assert twin["plan"]["name"] == "Omnichannel Suite Plan"
    assert twin["plan"]["billing_frequency"] == "MONTHLY"
    assert Decimal(twin["plan"]["current_catalog_price"]) == Decimal("7500.00")

    # Verify Subscription Items Snapshot
    assert len(twin["subscription_items"]) == 1
    # unit price = 3000 + 1200 = 4200.00; line_total = 2 * 4200 = 8400.00
    assert Decimal(twin["subscription_items"][0]["unit_price_snapshot"]) == Decimal("4200.00")
    assert Decimal(twin["contractual_recurring_price"]) == Decimal("8400.00")

    # Verify Quotation
    assert len(twin["quotations"]) == 1
    assert twin["quotations"][0]["id"] == q_id

    # Verify Invoices & Payments
    assert len(twin["invoices"]) == 1
    assert twin["invoices"][0]["invoice_number"] == "INV-2026-TWIN-001"
    assert twin["invoices"][0]["verification_status"] == "VERIFIED"
    assert len(twin["payments"]) == 1
    assert twin["payments"][0]["payment_method"] == "UPI_AUTOPAY"
    assert twin["verification_status"] == "VERIFIED"

    # Verify Change History
    assert len(twin["subscription_change_history"]) >= 2
    types = [e["event_type"] for e in twin["subscription_change_history"]]
    assert "ACTIVATED" in types
    assert "QUOTATION_CONVERTED" in types
