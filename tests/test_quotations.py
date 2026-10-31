from decimal import Decimal
from datetime import date, timedelta
import pytest


def test_quotation_lifecycle_and_conversion(client):
    # Setup Customer
    cust_resp = client.post(
        "/api/v1/customers",
        json={
            "customer_code": "CUST-QTN-1",
            "company_name": "Tata Consultancy Services",
            "contact_name": "Priya Nair",
            "email": "priya.nair@tcs.com",
            "status": "ACTIVE",
        },
    )
    cust_id = cust_resp.json()["id"]

    # Setup Plan
    plan_resp = client.post(
        "/api/v1/plans",
        json={
            "name": "Cloud Pro Plan",
            "billing_frequency": "MONTHLY",
            "plan_price": "5000.00",
            "status": "ACTIVE",
        },
    )
    plan_id = plan_resp.json()["id"]

    # Setup Product & Variant
    prod_resp = client.post(
        "/api/v1/products",
        json={
            "name": "VERISUB Core License",
            "product_type": "SAAS",
            "sales_price": "2000.00",
            "status": "ACTIVE",
            "variants": [
                {
                    "variant_name": "Priority Support",
                    "additional_price": "500.00",
                    "status": "ACTIVE",
                }
            ],
        },
    )
    prod_data = prod_resp.json()
    prod_id = prod_data["id"]
    var_id = prod_data["variants"][0]["id"]

    # 1. Create Quotation:
    # Item 1: 2 units of Core License + Priority Support (unit_price = 2000 + 500 = 2500, line_total = 5000)
    # Tax: GST_18 (18%)
    qtn_payload = {
        "customer_id": cust_id,
        "expiry_date": str(date.today() + timedelta(days=15)),
        "discount_total": "500.00",
        "notes": "Special enterprise introductory quote",
        "items": [
            {
                "product_id": prod_id,
                "variant_id": var_id,
                "plan_id": plan_id,
                "quantity": 2,
                "tax_configuration_reference": "GST_18",
            }
        ],
    }
    q_resp = client.post("/api/v1/quotations", json=qtn_payload)
    assert q_resp.status_code == 201
    q_data = q_resp.json()
    q_id = q_data["id"]

    # Verify calculation:
    # subtotal = 2 * 2500.00 = 5000.00
    # discount = 500.00
    # taxable = 4500.00
    # tax (18% of 4500) = 810.00
    # grand_total = 4500 + 810 = 5310.00
    assert Decimal(q_data["subtotal"]) == Decimal("5000.00")
    assert Decimal(q_data["discount_total"]) == Decimal("500.00")
    assert Decimal(q_data["tax_total"]) == Decimal("810.00")
    assert Decimal(q_data["grand_total"]) == Decimal("5310.00")
    assert q_data["status"] == "DRAFT"

    # 2. Update Draft Quotation (cannot update if confirmed)
    upd_resp = client.patch(f"/api/v1/quotations/{q_id}", json={"discount_total": "1000.00"})
    assert upd_resp.status_code == 200
    upd_data = upd_resp.json()
    # subtotal = 5000.00, discount = 1000.00, taxable = 4000.00, tax 18% = 720.00, grand = 4720.00
    assert Decimal(upd_data["discount_total"]) == Decimal("1000.00")
    assert Decimal(upd_data["tax_total"]) == Decimal("720.00")
    assert Decimal(upd_data["grand_total"]) == Decimal("4720.00")

    # 3. Confirm Quotation
    conf_resp = client.post(f"/api/v1/quotations/{q_id}/confirm")
    assert conf_resp.status_code == 200
    assert conf_resp.json()["status"] == "CONFIRMED"

    # Attempt to modify confirmed quotation must fail
    fail_upd = client.patch(f"/api/v1/quotations/{q_id}", json={"discount_total": "200.00"})
    assert fail_upd.status_code == 400
    assert "Only DRAFT quotations can be modified" in fail_upd.json()["detail"]

    # 4. Now modify base product price in catalog to verify snapshots remain immutable!
    client.patch(f"/api/v1/products/{prod_id}", json={"sales_price": "9999.00"})

    # 5. Convert confirmed quotation to subscription
    conv_resp = client.post(f"/api/v1/quotations/{q_id}/convert-to-subscription")
    assert conv_resp.status_code == 200
    conv_data = conv_resp.json()
    sub_id = conv_data["subscription_id"]

    # Verify quotation status is CONVERTED
    q_after = client.get(f"/api/v1/quotations/{q_id}").json()
    assert q_after["status"] == "CONVERTED"

    # Verify subscription has locked the snapshot unit price (2500.00), NOT the updated product price (9999.00)!
    sub_resp = client.get(f"/api/v1/subscriptions/{sub_id}").json()
    assert sub_resp["status"] == "CONFIRMED"
    assert len(sub_resp["items"]) == 1
    assert Decimal(sub_resp["items"][0]["unit_price_snapshot"]) == Decimal("2500.00")


def test_quotation_expiry_validation(client):
    cust_resp = client.post(
        "/api/v1/customers",
        json={"customer_code": "CUST-EXP-1", "contact_name": "Test", "email": "exp@test.com", "status": "ACTIVE"},
    )
    cust_id = cust_resp.json()["id"]

    prod_resp = client.post(
        "/api/v1/products",
        json={"name": "Prod Exp", "sales_price": "100.00", "status": "ACTIVE"},
    )
    prod_id = prod_resp.json()["id"]

    # Expired quotation (yesterday)
    q_resp = client.post(
        "/api/v1/quotations",
        json={
            "customer_id": cust_id,
            "expiry_date": str(date.today() - timedelta(days=1)),
            "items": [{"product_id": prod_id, "quantity": 1}],
        },
    )
    assert q_resp.status_code == 201
    q_id = q_resp.json()["id"]

    # Attempting to confirm must fail due to expiration
    resp_conf = client.post(f"/api/v1/quotations/{q_id}/confirm")
    assert resp_conf.status_code == 422
    assert "expired" in resp_conf.json()["detail"].lower()


def test_quotation_cancellation(client):
    cust_resp = client.post(
        "/api/v1/customers",
        json={"customer_code": "CUST-CNC-1", "contact_name": "Test", "email": "cnc@test.com", "status": "ACTIVE"},
    )
    cust_id = cust_resp.json()["id"]
    prod_resp = client.post(
        "/api/v1/products",
        json={"name": "Prod Cnc", "sales_price": "100.00", "status": "ACTIVE"},
    )
    prod_id = prod_resp.json()["id"]

    q_resp = client.post(
        "/api/v1/quotations",
        json={
            "customer_id": cust_id,
            "expiry_date": str(date.today() + timedelta(days=10)),
            "items": [{"product_id": prod_id, "quantity": 1}],
        },
    )
    q_id = q_resp.json()["id"]

    # Cancel quotation
    resp_cancel = client.post(f"/api/v1/quotations/{q_id}/cancel")
    assert resp_cancel.status_code == 200
    assert resp_cancel.json()["status"] == "CANCELLED"
