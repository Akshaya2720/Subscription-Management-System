from decimal import Decimal
from datetime import date, timedelta
import pytest


def test_product_change_impact_analysis(client):
    # Customer
    cust_resp = client.post(
        "/api/v1/customers",
        json={"customer_code": "CUST-IMP-01", "contact_name": "Kavita Singh", "email": "kavita@test.com", "status": "ACTIVE"},
    )
    cust_id = cust_resp.json()["id"]

    # Plan
    plan_resp = client.post(
        "/api/v1/plans",
        json={"name": "Basic SaaS Plan", "billing_frequency": "MONTHLY", "plan_price": "1000.00", "status": "ACTIVE"},
    )
    plan_id = plan_resp.json()["id"]

    # Product
    prod_resp = client.post(
        "/api/v1/products",
        json={"name": "Cloud Storage Module", "sales_price": "800.00", "status": "ACTIVE"},
    )
    prod_id = prod_resp.json()["id"]

    # Active Subscription 1 (quantity: 3, price: 800 -> 2400.00)
    sub1 = client.post(
        "/api/v1/subscriptions",
        json={
            "customer_id": cust_id,
            "plan_id": plan_id,
            "items": [{"product_id": prod_id, "quantity": 3}],
        },
    ).json()
    client.post(f"/api/v1/subscriptions/{sub1['id']}/activate")

    # Pending Quotation
    client.post(
        "/api/v1/quotations",
        json={
            "customer_id": cust_id,
            "expiry_date": str(date.today() + timedelta(days=10)),
            "items": [{"product_id": prod_id, "quantity": 1}],
        },
    )

    # Preview Impact of price hike from 800 to 1200
    impact_resp = client.post(
        "/api/v1/change-impact/product",
        json={
            "product_id": prod_id,
            "proposed_sales_price": "1200.00",
            "proposed_status": "ACTIVE",
        },
    )
    assert impact_resp.status_code == 200
    report = impact_resp.json()

    assert report["active_subscriptions_count"] == 1
    assert Decimal(report["contractual_monthly_revenue_protected"]) == Decimal("2400.00")
    assert report["affected_active_subscriptions"][0]["retains_contract_price"] is True
    assert Decimal(report["affected_active_subscriptions"][0]["contracted_unit_price"]) == Decimal("800.00")
    assert report["pending_quotations_count"] == 1
    assert "retain their agreed snapshot price" in report["business_policy_notice"]

    # Verify original product catalog price was NOT modified!
    original_prod = client.get(f"/api/v1/products/{prod_id}").json()
    assert Decimal(original_prod["sales_price"]) == Decimal("800.00")


def test_plan_change_impact_analysis(client):
    cust_resp = client.post(
        "/api/v1/customers",
        json={"customer_code": "CUST-IMP-02", "contact_name": "Arjun Das", "email": "arjun@test.com", "status": "ACTIVE"},
    )
    cust_id = cust_resp.json()["id"]

    plan_resp = client.post(
        "/api/v1/plans",
        json={"name": "Starter Tier", "billing_frequency": "MONTHLY", "plan_price": "1500.00", "status": "ACTIVE"},
    )
    plan_id = plan_resp.json()["id"]

    prod_resp = client.post(
        "/api/v1/products",
        json={"name": "Starter Core", "sales_price": "1500.00", "status": "ACTIVE"},
    )
    prod_id = prod_resp.json()["id"]

    # Create & Activate Subscription
    sub_resp = client.post(
        "/api/v1/subscriptions",
        json={
            "customer_id": cust_id,
            "plan_id": plan_id,
            "items": [{"product_id": prod_id, "quantity": 1}],
        },
    ).json()
    client.post(f"/api/v1/subscriptions/{sub_resp['id']}/activate")

    # Preview Impact of plan deactivation and price change
    impact_resp = client.post(
        "/api/v1/change-impact/plan",
        json={
            "plan_id": plan_id,
            "proposed_plan_price": "1999.00",
            "proposed_status": "ARCHIVED",
        },
    )
    assert impact_resp.status_code == 200
    report = impact_resp.json()

    assert report["active_subscriptions_count"] == 1
    assert Decimal(report["contractual_revenue_protected"]) == Decimal("1500.00")
    assert report["affected_active_subscriptions"][0]["retains_contract_price"] is True
    assert "Deactivating this plan will block new subscriber intake" in report["business_policy_notice"]
