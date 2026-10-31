from fastapi.testclient import TestClient
from app.core.database import get_db
from app.core.auth import get_current_organization
from app.main import app


def test_cross_organization_isolation(db_session, org_a, org_b):
    # Setup Client for Org A
    def get_db_override():
        try:
            yield db_session
        finally:
            pass

    def get_org_a():
        return org_a

    def get_org_b():
        return org_b

    # Org A operations
    app.dependency_overrides[get_db] = get_db_override
    app.dependency_overrides[get_current_organization] = get_org_a

    with TestClient(app) as client_a:
        # Create Customer in Org A
        cust_a = client_a.post(
            "/api/v1/customers",
            json={"customer_code": "CUST-ORGA-1", "contact_name": "Org A Contact", "email": "a@orga.com", "status": "ACTIVE"},
        ).json()

        # Create Product in Org A
        prod_a = client_a.post(
            "/api/v1/products",
            json={"name": "Org A Product", "sales_price": "100.00", "status": "ACTIVE"},
        ).json()

        # Create Plan in Org A
        plan_a = client_a.post(
            "/api/v1/plans",
            json={"name": "Org A Plan", "billing_frequency": "MONTHLY", "plan_price": "500.00", "status": "ACTIVE"},
        ).json()

        # Create Subscription in Org A
        sub_a = client_a.post(
            "/api/v1/subscriptions",
            json={
                "customer_id": cust_a["id"],
                "plan_id": plan_a["id"],
                "items": [{"product_id": prod_a["id"], "quantity": 1}],
            },
        ).json()

    # Now switch to Client for Org B
    app.dependency_overrides[get_current_organization] = get_org_b

    with TestClient(app) as client_b:
        # 1. Org B cannot see Org A's customer
        resp_cust = client_b.get(f"/api/v1/customers/{cust_a['id']}")
        assert resp_cust.status_code == 404

        # 2. Org B cannot see Org A's product
        resp_prod = client_b.get(f"/api/v1/products/{prod_a['id']}")
        assert resp_prod.status_code == 404

        # 3. Org B cannot see Org A's plan
        resp_plan = client_b.get(f"/api/v1/plans/{plan_a['id']}")
        assert resp_plan.status_code == 404

        # 4. Org B cannot see or manipulate Org A's subscription
        resp_sub = client_b.get(f"/api/v1/subscriptions/{sub_a['id']}")
        assert resp_sub.status_code == 404

        resp_act = client_b.post(f"/api/v1/subscriptions/{sub_a['id']}/activate")
        assert resp_act.status_code == 404

        # 5. Org B customer listing is empty (Org A's customers excluded)
        resp_list = client_b.get("/api/v1/customers")
        assert resp_list.status_code == 200
        assert resp_list.json()["total"] == 0

    app.dependency_overrides.clear()
