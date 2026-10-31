import pytest


def test_customer_crud(client):
    # 1. Create Customer
    payload = {
        "customer_code": "CUST-001",
        "company_name": "Infosys Technologies",
        "contact_name": "Aarav Sharma",
        "email": "aarav.sharma@infosys.com",
        "phone": "+91 9876543210",
        "billing_address": "Electronics City, Bengaluru, Karnataka, India",
        "tax_identifier": "29AABCU9603R1ZM",
        "status": "ACTIVE",
    }
    resp = client.post("/api/v1/customers", json=payload)
    assert resp.status_code == 201
    cust_data = resp.json()
    cust_id = cust_data["id"]
    assert cust_data["customer_code"] == "CUST-001"
    assert cust_data["company_name"] == "Infosys Technologies"

    # 2. Get Customer by ID
    resp_get = client.get(f"/api/v1/customers/{cust_id}")
    assert resp_get.status_code == 200
    assert resp_get.json()["email"] == "aarav.sharma@infosys.com"

    # 3. Update Customer
    update_payload = {
        "contact_name": "Aarav K. Sharma",
        "phone": "+91 9999988888",
    }
    resp_update = client.patch(f"/api/v1/customers/{cust_id}", json=update_payload)
    assert resp_update.status_code == 200
    assert resp_update.json()["contact_name"] == "Aarav K. Sharma"
    assert resp_update.json()["phone"] == "+91 9999988888"

    # 4. Deactivate Customer
    resp_delete = client.delete(f"/api/v1/customers/{cust_id}")
    assert resp_delete.status_code == 200
    assert resp_delete.json()["status"] == "INACTIVE"


def test_duplicate_customer_handling(client):
    payload = {
        "customer_code": "CUST-DUP-1",
        "company_name": "Wipro",
        "contact_name": "Rohan Patel",
        "email": "rohan@wipro.com",
        "status": "ACTIVE",
    }
    resp1 = client.post("/api/v1/customers", json=payload)
    assert resp1.status_code == 201

    # Attempt duplicate customer_code
    dup_code_payload = {
        "customer_code": "CUST-DUP-1",
        "company_name": "Another Company",
        "contact_name": "Rohan Patel",
        "email": "another@wipro.com",
        "status": "ACTIVE",
    }
    resp_dup_code = client.post("/api/v1/customers", json=dup_code_payload)
    assert resp_dup_code.status_code == 409
    assert "Customer code 'CUST-DUP-1' already exists" in resp_dup_code.json()["detail"]

    # Attempt duplicate email
    dup_email_payload = {
        "customer_code": "CUST-DUP-2",
        "company_name": "Another Company 2",
        "contact_name": "Rohan Patel",
        "email": "rohan@wipro.com",
        "status": "ACTIVE",
    }
    resp_dup_email = client.post("/api/v1/customers", json=dup_email_payload)
    assert resp_dup_email.status_code == 409
    assert "Customer email 'rohan@wipro.com' already exists" in resp_dup_email.json()["detail"]


def test_customer_search_filter_pagination(client):
    for i in range(1, 11):
        status_val = "ACTIVE" if i <= 7 else "SUSPENDED"
        client.post(
            "/api/v1/customers",
            json={
                "customer_code": f"CUST-PAG-{i:03d}",
                "company_name": f"Enterprise Corp {i}",
                "contact_name": f"Contact Person {i}",
                "email": f"contact{i}@enterprise.com",
                "status": status_val,
            },
        )

    # Search
    resp_search = client.get("/api/v1/customers?search=Enterprise Corp 5")
    assert resp_search.status_code == 200
    assert resp_search.json()["total"] == 1
    assert resp_search.json()["items"][0]["customer_code"] == "CUST-PAG-005"

    # Filter by status
    resp_filter = client.get("/api/v1/customers?status=SUSPENDED")
    assert resp_filter.status_code == 200
    assert resp_filter.json()["total"] == 3

    # Pagination
    resp_pag = client.get("/api/v1/customers?page=1&per_page=4")
    assert resp_pag.status_code == 200
    assert len(resp_pag.json()["items"]) == 4
    assert resp_pag.json()["total"] == 10
    assert resp_pag.json()["pages"] == 3
