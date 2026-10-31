import uuid
from datetime import date, timedelta
from decimal import Decimal
import pytest
from app.modules.billing.models import TaxRule, Discount
from app.modules.billing.taxes import TaxService
from app.modules.billing.discounts import DiscountService


def test_tax_rules_and_calculations(client, db_session, org_a):
    """Test tax rule creation, inclusive vs exclusive calculation, and breakdown."""
    # 1. Create exclusive GST 18% rule via API
    resp_gst = client.post(
        "/api/v1/tax-rules",
        json={
            "name": "GST 18%",
            "tax_rate": "0.1800",
            "tax_type": "GST",
            "inclusive_or_exclusive": "EXCLUSIVE",
            "effective_from": str(date.today()),
            "active": True,
        },
    )
    assert resp_gst.status_code == 201
    gst_rule_id = resp_gst.json()["id"]

    # 2. Create second exclusive Cess 2% rule
    resp_cess = client.post(
        "/api/v1/tax-rules",
        json={
            "name": "Clean Energy Cess 2%",
            "tax_rate": "0.0200",
            "tax_type": "CESS",
            "inclusive_or_exclusive": "EXCLUSIVE",
            "effective_from": str(date.today()),
            "active": True,
        },
    )
    assert resp_cess.status_code == 201

    # 3. Test exclusive calculation
    tax_rules = TaxService.get_tax_rules(db_session, org_a.id, active_only=True)
    assert len(tax_rules) == 2

    subtotal = Decimal("1000.00")
    taxable_base, total_tax, breakdown = TaxService.calculate_taxes(subtotal, tax_rules)
    assert taxable_base == Decimal("1000.00")
    assert total_tax == Decimal("200.00")  # 18% + 2% of 1000
    assert breakdown["GST 18%"] == Decimal("180.00")
    assert breakdown["Clean Energy Cess 2%"] == Decimal("20.00")

    # 4. Test tax-inclusive calculation
    rule_inc = TaxRule(
        id=uuid.uuid4(),
        organization_id=org_a.id,
        name="VAT 10% Inclusive",
        tax_rate=Decimal("0.1000"),
        tax_type="VAT",
        inclusive_or_exclusive="INCLUSIVE",
        effective_from=date.today(),
        active=True,
    )
    inc_base, inc_tax, inc_breakdown = TaxService.calculate_taxes(Decimal("110.00"), [rule_inc])
    # 110 / 1.10 = 100 base, 10 tax
    assert inc_base == Decimal("100.00")
    assert inc_tax == Decimal("10.00")
    assert inc_breakdown["VAT 10% Inclusive"] == Decimal("10.00")

    # 5. Patch tax rule
    patch_resp = client.patch(
        f"/api/v1/tax-rules/{gst_rule_id}",
        json={"tax_rate": "0.1200", "name": "GST 12%"},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["tax_rate"] == "0.1200"


def test_discount_rules_and_limits(client, db_session, org_a):
    """Test fixed/percentage discounts, date expiration, minimum purchase, and usage limits."""
    today = date.today()

    # 1. Create a percentage discount with usage limit of 2 redemptions
    resp_disc = client.post(
        "/api/v1/discounts",
        json={
            "discount_name": "Early Bird 15%",
            "discount_code": "EARLY15",
            "discount_type": "PERCENTAGE",
            "discount_value": "15.00",
            "minimum_purchase": "500.00",
            "minimum_quantity": 2,
            "start_date": str(today - timedelta(days=5)),
            "end_date": str(today + timedelta(days=10)),
            "usage_limit": 2,
            "active": True,
        },
    )
    assert resp_disc.status_code == 201
    disc_id = resp_disc.json()["id"]
    disc_uuid = uuid.UUID(disc_id)

    # 2. Validate discount with subtotal below minimum purchase -> should fail
    resp_val_fail = client.post(
        f"/api/v1/discounts/{disc_id}/validate",
        json={"purchase_subtotal": "300.00", "quantity": 2},
    )
    assert resp_val_fail.status_code == 200
    assert resp_val_fail.json()["eligible"] is False
    assert "Minimum purchase amount" in resp_val_fail.json()["reason"]

    # 3. Validate with quantity below minimum -> should fail
    resp_val_qty_fail = client.post(
        f"/api/v1/discounts/{disc_id}/validate",
        json={"purchase_subtotal": "800.00", "quantity": 1},
    )
    assert resp_val_qty_fail.status_code == 200
    assert resp_val_qty_fail.json()["eligible"] is False
    assert "Minimum quantity" in resp_val_qty_fail.json()["reason"]

    # 4. Validate with valid conditions -> eligible
    resp_val_ok = client.post(
        f"/api/v1/discounts/{disc_id}/validate",
        json={"purchase_subtotal": "1000.00", "quantity": 3},
    )
    assert resp_val_ok.status_code == 200
    assert resp_val_ok.json()["eligible"] is True
    assert resp_val_ok.json()["estimated_discount_amount"] == 150.0  # 15% of 1000

    # 5. Test usage limit exhaustion with valid foreign key records
    from app.modules.customers.models import Customer
    from app.modules.billing.models import Invoice

    cust = Customer(
        id=uuid.uuid4(),
        organization_id=org_a.id,
        customer_code="CUST-DISC-01",
        contact_name="Discount User",
        company_name="Discount Co",
        email="disc@discount.com",
        status="ACTIVE",
    )
    inv = Invoice(
        id=uuid.uuid4(),
        organization_id=org_a.id,
        customer_id=cust.id,
        invoice_number="INV-DISC-001",
        issue_date=today,
        due_date=today,
        subtotal=Decimal("1000.00"),
        total_amount=Decimal("1000.00"),
        amount_paid=Decimal("0.00"),
        amount_due=Decimal("1000.00"),
        status="DRAFT",
    )
    db_session.add_all([cust, inv])
    db_session.commit()

    # Redemption 1
    redemp1 = DiscountService.redeem_discount(
        db_session, disc_uuid, inv.id, cust.id, Decimal("150.00")
    )
    assert redemp1 is not None
    # Redemption 2
    redemp2 = DiscountService.redeem_discount(
        db_session, disc_uuid, inv.id, cust.id, Decimal("150.00")
    )
    assert redemp2 is not None
    # Redemption 3 -> should fail due to usage limit = 2
    redemp3 = DiscountService.redeem_discount(
        db_session, disc_uuid, inv.id, cust.id, Decimal("150.00")
    )
    assert redemp3 is None

    # Validate endpoint now reports usage limit reached
    resp_val_exhausted = client.post(
        f"/api/v1/discounts/{disc_id}/validate",
        json={"purchase_subtotal": "1000.00", "quantity": 3},
    )
    assert resp_val_exhausted.json()["eligible"] is False
    assert "usage limit" in resp_val_exhausted.json()["reason"]
