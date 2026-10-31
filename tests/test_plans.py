from decimal import Decimal
from datetime import date, timedelta
import pytest


def test_plan_crud_and_price_history(client):
    # 1. Create Subscription Plan
    plan_payload = {
        "name": "Standard Enterprise Monthly",
        "description": "Standard monthly SaaS tier",
        "billing_frequency": "MONTHLY",
        "plan_price": "2999.00",
        "minimum_quantity": 1,
        "start_availability_date": str(date.today() - timedelta(days=5)),
        "end_availability_date": str(date.today() + timedelta(days=365)),
        "auto_close_configuration": {"max_failed_payments": 3},
        "early_closure_configuration": {"penalty_fee": "500.00"},
        "pause_configuration": {"max_pause_days": 60},
        "renewal_configuration": {"auto_renew": True},
        "status": "ACTIVE",
    }
    resp = client.post("/api/v1/plans", json=plan_payload)
    assert resp.status_code == 201
    plan_data = resp.json()
    plan_id = plan_data["id"]
    assert plan_data["name"] == "Standard Enterprise Monthly"
    assert Decimal(plan_data["plan_price"]) == Decimal("2999.00")
    assert len(plan_data["price_history"]) == 1

    # 2. Update Plan Price: 2999.00 -> 3499.00
    upd_resp = client.patch(f"/api/v1/plans/{plan_id}", json={"plan_price": "3499.00"})
    assert upd_resp.status_code == 200
    assert Decimal(upd_resp.json()["plan_price"]) == Decimal("3499.00")

    # 3. Verify price history audit trail
    hist_resp = client.get(f"/api/v1/plans/{plan_id}/price-history")
    assert hist_resp.status_code == 200
    hist_items = hist_resp.json()
    assert len(hist_items) == 2
    # Latest first
    assert Decimal(hist_items[0]["price"]) == Decimal("3499.00")
    assert Decimal(hist_items[1]["price"]) == Decimal("2999.00")


def test_plan_frequency_validation(client):
    # Invalid billing frequency
    invalid_payload = {
        "name": "Invalid Frequency Plan",
        "billing_frequency": "BIWEEKLY",  # Not supported
        "plan_price": "100.00",
        "status": "ACTIVE",
    }
    resp = client.post("/api/v1/plans", json=invalid_payload)
    assert resp.status_code == 422


def test_plan_availability_date_validation(client):
    # start date after end date
    invalid_dates_payload = {
        "name": "Invalid Date Plan",
        "billing_frequency": "YEARLY",
        "plan_price": "10000.00",
        "start_availability_date": str(date.today() + timedelta(days=30)),
        "end_availability_date": str(date.today()),  # earlier than start
        "status": "ACTIVE",
    }
    resp = client.post("/api/v1/plans", json=invalid_dates_payload)
    assert resp.status_code == 422
