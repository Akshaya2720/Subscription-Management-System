from decimal import Decimal
import pytest


def test_product_crud_and_variants(client):
    # 1. Create Product: Odoo (sales_price: 1500.00)
    prod_payload = {
        "name": "Odoo Enterprise",
        "product_type": "SAAS",
        "description": "All-in-one business management software",
        "sales_price": "1500.00",
        "cost_price": "800.00",
        "notes": "Annual or monthly subscription available",
        "status": "ACTIVE",
        "variants": [
            {
                "variant_name": "Premium Support",
                "description": "24/7 dedicated telephone and live support",
                "additional_price": "560.00",
                "status": "ACTIVE",
            }
        ],
    }
    resp = client.post("/api/v1/products", json=prod_payload)
    assert resp.status_code == 201
    prod_data = resp.json()
    prod_id = prod_data["id"]
    assert prod_data["name"] == "Odoo Enterprise"
    assert Decimal(prod_data["sales_price"]) == Decimal("1500.00")
    assert len(prod_data["variants"]) == 1
    assert prod_data["variants"][0]["variant_name"] == "Premium Support"
    assert Decimal(prod_data["variants"][0]["additional_price"]) == Decimal("560.00")

    # 2. Get Product
    resp_get = client.get(f"/api/v1/products/{prod_id}")
    assert resp_get.status_code == 200
    assert resp_get.json()["name"] == "Odoo Enterprise"

    # 3. Add second variant: Cloud Hosting (+ ₹300)
    var_payload = {
        "variant_name": "Dedicated Cloud Hosting",
        "description": "Private AWS instance",
        "additional_price": "300.00",
        "status": "ACTIVE",
    }
    resp_var = client.post(f"/api/v1/products/{prod_id}/variants", json=var_payload)
    assert resp_var.status_code == 201
    var_data = resp_var.json()
    var_id = var_data["id"]
    assert var_data["variant_name"] == "Dedicated Cloud Hosting"
    assert Decimal(var_data["additional_price"]) == Decimal("300.00")

    # 4. List variants for product
    resp_vars = client.get(f"/api/v1/products/{prod_id}/variants")
    assert resp_vars.status_code == 200
    assert len(resp_vars.json()) == 2

    # 5. Update variant price
    resp_var_upd = client.patch(f"/api/v1/variants/{var_id}", json={"additional_price": "350.00"})
    assert resp_var_upd.status_code == 200
    assert Decimal(resp_var_upd.json()["additional_price"]) == Decimal("350.00")

    # 6. Deactivate variant
    resp_var_del = client.delete(f"/api/v1/variants/{var_id}")
    assert resp_var_del.status_code == 200
    assert resp_var_del.json()["status"] == "INACTIVE"

    # 7. Update Product
    resp_prod_upd = client.patch(f"/api/v1/products/{prod_id}", json={"sales_price": "1650.00"})
    assert resp_prod_upd.status_code == 200
    assert Decimal(resp_prod_upd.json()["sales_price"]) == Decimal("1650.00")

    # 8. Deactivate / Archive product
    resp_prod_del = client.delete(f"/api/v1/products/{prod_id}")
    assert resp_prod_del.status_code == 200
    assert resp_prod_del.json()["status"] == "ARCHIVED"


def test_duplicate_product_name(client):
    payload = {
        "name": "QuickBooks Connector",
        "product_type": "SAAS",
        "sales_price": "999.00",
        "status": "ACTIVE",
    }
    resp1 = client.post("/api/v1/products", json=payload)
    assert resp1.status_code == 201

    resp2 = client.post("/api/v1/products", json=payload)
    assert resp2.status_code == 409
    assert "already exists" in resp2.json()["detail"]


def test_product_search_and_filter(client):
    client.post(
        "/api/v1/products",
        json={"name": "CRM Core", "product_type": "SAAS", "sales_price": "100.00", "status": "ACTIVE"},
    )
    client.post(
        "/api/v1/products",
        json={"name": "Consulting Hours", "product_type": "SERVICE", "sales_price": "200.00", "status": "ACTIVE"},
    )
    client.post(
        "/api/v1/products",
        json={"name": "Legacy Tool", "product_type": "LICENSE", "sales_price": "50.00", "status": "ARCHIVED"},
    )

    # Filter by product_type
    resp_type = client.get("/api/v1/products?product_type=SERVICE")
    assert resp_type.status_code == 200
    assert resp_type.json()["total"] == 1
    assert resp_type.json()["items"][0]["name"] == "Consulting Hours"

    # Filter by status
    resp_arch = client.get("/api/v1/products?status=ARCHIVED")
    assert resp_arch.status_code == 200
    assert resp_arch.json()["total"] == 1
    assert resp_arch.json()["items"][0]["name"] == "Legacy Tool"
