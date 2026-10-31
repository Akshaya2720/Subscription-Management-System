from decimal import Decimal
from datetime import date, timedelta
import pytest


def test_subscription_complete_lifecycle(client):
    # Setup Customer
    cust_resp = client.post(
        "/api/v1/customers",
        json={
            "customer_code": "CUST-SUB-001",
            "company_name": "Zoho Partner Corp",
            "contact_name": "Siddharth Rao",
            "email": "sid@zoho.com",
            "status": "ACTIVE",
        },
    )
    cust_id = cust_resp.json()["id"]

    # Setup Plan (Monthly)
    plan_resp = client.post(
        "/api/v1/plans",
        json={
            "name": "Growth Monthly Plan",
            "billing_frequency": "MONTHLY",
            "plan_price": "4000.00",
            "minimum_quantity": 1,
            "status": "ACTIVE",
        },
    )
    plan_id = plan_resp.json()["id"]

    # Setup Product
    prod_resp = client.post(
        "/api/v1/products",
        json={
            "name": "Analytics Add-on",
            "product_type": "SAAS",
            "sales_price": "1200.00",
            "status": "ACTIVE",
        },
    )
    prod_id = prod_resp.json()["id"]

    # 1. Create Subscription in DRAFT
    sub_payload = {
        "customer_id": cust_id,
        "plan_id": plan_id,
        "start_date": str(date.today()),
        "billing_frequency": "MONTHLY",
        "payment_terms": "NET_30",
        "currency": "INR",
        "renewal_enabled": True,
        "items": [
            {
                "product_id": prod_id,
                "quantity": 2,
                "unit_price_snapshot": "1200.00",
            }
        ],
    }
    resp = client.post("/api/v1/subscriptions", json=sub_payload)
    assert resp.status_code == 201
    sub_data = resp.json()
    sub_id = sub_data["id"]
    assert sub_data["status"] == "DRAFT"
    assert sub_data["billing_frequency"] == "MONTHLY"
    # next_billing_date is 1 month from start_date
    assert sub_data["next_billing_date"] is not None

    # 2. Activate Subscription: DRAFT -> ACTIVE
    act_resp = client.post(f"/api/v1/subscriptions/{sub_id}/activate")
    assert act_resp.status_code == 200
    assert act_resp.json()["status"] == "ACTIVE"

    # 3. Pause Subscription: ACTIVE -> PAUSED
    pause_payload = {
        "reason": "Temporary customer maintenance window",
        "resume_date": str(date.today() + timedelta(days=14)),
    }
    pause_resp = client.post(f"/api/v1/subscriptions/{sub_id}/pause", json=pause_payload)
    assert pause_resp.status_code == 200
    assert pause_resp.json()["status"] == "PAUSED"
    assert pause_resp.json()["pause_information"]["reason"] == "Temporary customer maintenance window"

    # 4. Resume Subscription: PAUSED -> ACTIVE
    resume_resp = client.post(f"/api/v1/subscriptions/{sub_id}/resume", json={"notes": "Maintenance finished early"})
    assert resume_resp.status_code == 200
    assert resume_resp.json()["status"] == "ACTIVE"
    assert resume_resp.json()["pause_information"] is None

    # 5. Renew Subscription: ACTIVE -> ACTIVE (advances next_billing_date)
    old_next_billing = resume_resp.json()["next_billing_date"]
    renew_resp = client.post(
        f"/api/v1/subscriptions/{sub_id}/renew",
        json={"extension_periods": 1, "notes": "Customer accepted renewal"},
    )
    assert renew_resp.status_code == 200
    assert renew_resp.json()["status"] == "ACTIVE"
    assert renew_resp.json()["next_billing_date"] != old_next_billing

    # 6. Close Subscription: ACTIVE -> CLOSED (with early closure fee)
    close_payload = {
        "reason": "Customer migration to dedicated on-prem",
        "early_closure_fee": "2500.00",
    }
    close_resp = client.post(f"/api/v1/subscriptions/{sub_id}/close", json=close_payload)
    assert close_resp.status_code == 200
    assert close_resp.json()["status"] == "CLOSED"
    assert close_resp.json()["closure_information"]["early_closure_fee"] == "2500.00"

    # 7. Check Events History
    events_resp = client.get(f"/api/v1/subscriptions/{sub_id}/events")
    assert events_resp.status_code == 200
    events = events_resp.json()
    # Expect: CLOSED, RENEWED, RESUMED, PAUSED, ACTIVATED, CREATED
    event_types = [e["event_type"] for e in events]
    assert "CREATED" in event_types
    assert "ACTIVATED" in event_types
    assert "PAUSED" in event_types
    assert "RESUMED" in event_types
    assert "RENEWED" in event_types
    assert "CLOSED" in event_types


def test_invalid_state_transitions(client):
    cust_resp = client.post(
        "/api/v1/customers",
        json={"customer_code": "CUST-INV-1", "contact_name": "Test", "email": "inv@test.com", "status": "ACTIVE"},
    )
    cust_id = cust_resp.json()["id"]

    plan_resp = client.post(
        "/api/v1/plans",
        json={"name": "Inv Plan", "billing_frequency": "YEARLY", "plan_price": "1000.00", "status": "ACTIVE"},
    )
    plan_id = plan_resp.json()["id"]

    prod_resp = client.post(
        "/api/v1/products",
        json={"name": "Inv Prod", "sales_price": "500.00", "status": "ACTIVE"},
    )
    prod_id = prod_resp.json()["id"]

    # Create subscription
    sub_resp = client.post(
        "/api/v1/subscriptions",
        json={
            "customer_id": cust_id,
            "plan_id": plan_id,
            "items": [{"product_id": prod_id, "quantity": 1}],
        },
    )
    sub_id = sub_resp.json()["id"]

    # 1. Cannot resume a DRAFT subscription (only PAUSED can be resumed)
    resp_bad_resume = client.post(f"/api/v1/subscriptions/{sub_id}/resume")
    assert resp_bad_resume.status_code == 400

    # 2. Cannot pause a DRAFT subscription (only ACTIVE can be paused)
    resp_bad_pause = client.post(f"/api/v1/subscriptions/{sub_id}/pause", json={"reason": "test"})
    assert resp_bad_pause.status_code == 400

    # 3. Cannot renew a DRAFT subscription
    resp_bad_renew = client.post(f"/api/v1/subscriptions/{sub_id}/renew")
    assert resp_bad_renew.status_code == 400

    # 4. Activate then close
    client.post(f"/api/v1/subscriptions/{sub_id}/activate")
    client.post(f"/api/v1/subscriptions/{sub_id}/close", json={"reason": "cancelled by user"})

    # 5. Cannot activate a CLOSED subscription
    resp_closed_act = client.post(f"/api/v1/subscriptions/{sub_id}/activate")
    assert resp_closed_act.status_code == 400
    assert "Invalid state transition" in resp_closed_act.json()["detail"]


def test_subscription_search_filter_pagination(client):
    cust_resp = client.post(
        "/api/v1/customers",
        json={"customer_code": "CUST-SUB-PAG", "contact_name": "Test", "email": "subpag@test.com", "status": "ACTIVE"},
    )
    cust_id = cust_resp.json()["id"]

    plan_resp = client.post(
        "/api/v1/plans",
        json={"name": "Sub Pag Plan", "billing_frequency": "MONTHLY", "plan_price": "1000.00", "status": "ACTIVE"},
    )
    plan_id = plan_resp.json()["id"]

    prod_resp = client.post(
        "/api/v1/products",
        json={"name": "Sub Pag Prod", "sales_price": "100.00", "status": "ACTIVE"},
    )
    prod_id = prod_resp.json()["id"]

    for i in range(5):
        client.post(
            "/api/v1/subscriptions",
            json={
                "customer_id": cust_id,
                "plan_id": plan_id,
                "items": [{"product_id": prod_id, "quantity": 1}],
            },
        )

    resp_list = client.get(f"/api/v1/subscriptions?customer_id={cust_id}&page=1&per_page=3")
    assert resp_list.status_code == 200
    assert resp_list.json()["total"] == 5
    assert len(resp_list.json()["items"]) == 3
