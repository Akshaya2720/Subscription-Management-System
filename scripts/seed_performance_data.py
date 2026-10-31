"""Performance seeding script for Phase 4 benchmarking.

Creates:
- 1 Organization
- 2 Users (1 ADMIN, 1 STAFF)
- 500 Customers
- 5 Products & Plans with Variants
- 1,000 Subscriptions
- 5,000 Invoices
- 3,000 Payments
- Initial Cryptographic SHA-256 Audit Chain
"""

import sys
import uuid
import time
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

# Ensure project root is in sys.path
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal, engine, Base
from app.core.security import hash_password
from app.models.auth import Organization, User, UserRole
from app.models.catalog import Product, ProductVariant, SubscriptionPlan
from app.models.customer import Customer
from app.models.subscription import Subscription, SubscriptionItem
from app.models.billing import Invoice, InvoiceItem, Payment, TaxRule, Discount, InvoiceStatus
from app.models.verification import AuditLog, VerificationContract
from app.modules.verification.service import AuditService


def seed_performance_data():
    start_time = time.time()
    print("🚀 Starting VeriSub High-Volume Performance Data Seeding...")

    # Ensure tables are initialized
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. Organization
        org = db.query(Organization).filter(Organization.name == "VeriSub Enterprise Cloud").first()
        if not org:
            org = Organization(
                name="VeriSub Enterprise Cloud",
                slug="verisub-enterprise",
                is_active=True,
            )
            db.add(org)
            db.flush()
            print(f"✓ Organization created: {org.name} ({org.id})")
        else:
            print(f"ℹ Reusing existing organization: {org.name} ({org.id})")

        org_id = org.id

        # 2. Users (Admin + Staff)
        admin_user = db.query(User).filter(User.email == "admin@verisub.cloud").first()
        if not admin_user:
            admin_user = User(
                organization_id=org_id,
                email="admin@verisub.cloud",
                password_hash=hash_password("Verisub#2026Admin"),
                full_name="Alex Mercer (Platform Admin)",
                role=UserRole.ADMIN,
                is_active=True,
            )
            db.add(admin_user)

        staff_user = db.query(User).filter(User.email == "staff@verisub.cloud").first()
        if not staff_user:
            staff_user = User(
                organization_id=org_id,
                email="staff@verisub.cloud",
                password_hash=hash_password("Verisub#2026Staff"),
                full_name="Sarah Jenkins (Billing Staff)",
                role=UserRole.STAFF,
                is_active=True,
            )
            db.add(staff_user)

        db.flush()
        print("✓ Admin and Staff users initialized.")

        # 3. Tax Rule & Discount
        tax_rule = db.query(TaxRule).filter(TaxRule.organization_id == org_id, TaxRule.name == "Standard US VAT").first()
        if not tax_rule:
            tax_rule = TaxRule(
                organization_id=org_id,
                name="Standard US VAT",
                tax_type="VAT",
                rate_percentage=Decimal("10.00"),
                country_code="US",
                is_default=True,
                is_active=True,
            )
            db.add(tax_rule)

        discount = db.query(Discount).filter(Discount.organization_id == org_id, Discount.code == "SCALE15").first()
        if not discount:
            discount = Discount(
                organization_id=org_id,
                code="SCALE15",
                name="Scale 15% Promotional Discount",
                discount_type="PERCENTAGE",
                discount_value=Decimal("15.00"),
                min_purchase_amount=Decimal("100.00"),
                min_quantity=1,
                start_date=date.today() - timedelta(days=60),
                end_date=date.today() + timedelta(days=300),
                is_active=True,
            )
            db.add(discount)

        # 4. Catalog: Products & Plans with Variants
        products_data = [
            ("Dedicated Cloud VM 8-Core", "SERVICE", Decimal("250.00"), Decimal("120.00")),
            ("High-Performance Postgres DB", "SERVICE", Decimal("500.00"), Decimal("220.00")),
            ("Distributed Storage Node 10TB", "SERVICE", Decimal("180.00"), Decimal("80.00")),
            ("Enterprise Edge AI Gateway", "SERVICE", Decimal("800.00"), Decimal("350.00")),
            ("Microservice Orchestrator Mesh", "SERVICE", Decimal("350.00"), Decimal("150.00")),
        ]

        products = []
        for name, prod_type, sales_price, cost_price in products_data:
            p = db.query(Product).filter(Product.organization_id == org_id, Product.name == name).first()
            if not p:
                p = Product(
                    organization_id=org_id,
                    name=name,
                    product_type=prod_type,
                    sales_price=sales_price,
                    cost_price=cost_price,
                    status="ACTIVE",
                )
                db.add(p)
                db.flush()

                # Add variant with price delta as per PDF requirement
                v1 = ProductVariant(
                    product_id=p.id,
                    variant_name="Odoo Enterprise Brand",
                    additional_price=Decimal("560.00"),
                    status="ACTIVE",
                )
                v2 = ProductVariant(
                    product_id=p.id,
                    variant_name="Standard Edition",
                    additional_price=Decimal("0.00"),
                    status="ACTIVE",
                )
                db.add_all([v1, v2])

            products.append(p)

        db.flush()

        # Plans
        plans = []
        frequencies = ["MONTHLY", "ANNUALLY", "MONTHLY", "WEEKLY", "MONTHLY"]
        for idx, p in enumerate(products):
            plan_name = f"{p.name} - Production Tier"
            plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.organization_id == org_id, SubscriptionPlan.name == plan_name).first()
            if not plan:
                plan = SubscriptionPlan(
                    organization_id=org_id,
                    name=plan_name,
                    plan_price=p.sales_price,
                    billing_frequency=frequencies[idx % len(frequencies)],
                    minimum_quantity=1,
                    is_auto_close_at_end=False,
                    is_closable_early=True,
                    is_pausable=True,
                    is_renewable=True,
                    status="ACTIVE",
                )
                db.add(plan)
                db.flush()
            plans.append(plan)

        print(f"✓ Products ({len(products)}) and Subscription Plans ({len(plans)}) ready.")

        # 5. Seed 500 Customers
        existing_cust_count = db.query(Customer).filter(Customer.organization_id == org_id).count()
        customers_to_create = 500 - existing_cust_count

        if customers_to_create > 0:
            print(f"⏳ Generating {customers_to_create} Customer accounts...")
            new_customers = []
            for i in range(existing_cust_count + 1, 501):
                cust = Customer(
                    organization_id=org_id,
                    customer_code=f"CUST-{i:04d}",
                    company_name=f"Partner Client {i:04d} Inc",
                    contact_name=f"Client Lead {i:04d}",
                    email=f"client{i:04d}@partnercloud.com",
                    billing_address=f"Suite {i:03d}, Tech Boulevard, Austin, TX",
                    status="ACTIVE",
                )
                new_customers.append(cust)

            db.bulk_save_objects(new_customers)
            db.commit()
            print(f"✓ 500 Customers committed to database.")

        customers = db.query(Customer).filter(Customer.organization_id == org_id).all()

        # 6. Seed 1,000 Subscriptions
        existing_sub_count = db.query(Subscription).filter(Subscription.organization_id == org_id).count()
        subs_to_create = 1000 - existing_sub_count

        if subs_to_create > 0:
            print(f"⏳ Generating {subs_to_create} Subscriptions with line items...")
            today = date.today()
            statuses = ["ACTIVE", "ACTIVE", "ACTIVE", "ACTIVE", "PAUSED", "CLOSED"]

            new_subs = []
            new_sub_items = []
            for i in range(existing_sub_count + 1, 1001):
                cust = customers[i % len(customers)]
                plan = plans[i % len(plans)]
                prod = products[i % len(products)]
                sub_status = statuses[i % len(statuses)]
                sub_id = uuid.uuid4()

                start = today - timedelta(days=(i % 180) + 10)
                next_bill = start + timedelta(days=30)
                while next_bill <= today:
                    next_bill += timedelta(days=30)

                sub = Subscription(
                    id=sub_id,
                    organization_id=org_id,
                    customer_id=cust.id,
                    plan_id=plan.id,
                    subscription_number=f"SUB-2026-{i:05d}",
                    start_date=start,
                    next_billing_date=next_bill,
                    billing_frequency=plan.billing_frequency,
                    payment_terms="NET_30",
                    status=sub_status,
                    currency="USD",
                    renewal_enabled=True,
                )
                new_subs.append(sub)

                item = SubscriptionItem(
                    subscription_id=sub_id,
                    product_id=prod.id,
                    description_snapshot=f"{prod.name} (Production)",
                    quantity=1 + (i % 3),
                    unit_price_snapshot=prod.sales_price,
                    line_total=prod.sales_price * Decimal(1 + (i % 3)),
                )
                new_sub_items.append(item)

            db.bulk_save_objects(new_subs)
            db.bulk_save_objects(new_sub_items)
            db.commit()
            print("✓ 1,000 Subscriptions committed to database.")

        subscriptions = db.query(Subscription).filter(Subscription.organization_id == org_id).all()

        # 7. Seed 5,000 Invoices
        existing_inv_count = db.query(Invoice).filter(Invoice.organization_id == org_id).count()
        invs_to_create = 5000 - existing_inv_count

        if invs_to_create > 0:
            print(f"⏳ Generating {invs_to_create} Invoices with itemized inclusions...")
            today = date.today()
            inv_statuses = ["PAID", "PAID", "PAID", "CONFIRMED", "DRAFT", "OVERDUE"]

            new_invoices = []
            new_inv_items = []
            for i in range(existing_inv_count + 1, 5001):
                sub = subscriptions[i % len(subscriptions)]
                cust = customers[i % len(customers)]
                st = inv_statuses[i % len(inv_statuses)]
                inv_id = uuid.uuid4()

                # Each invoice gets a distinct monthly billing cycle per subscription to satisfy UNIQUE constraint
                cycle = (i // len(subscriptions))  # 0, 1, 2, 3, 4
                period_start = today - timedelta(days=(5 - cycle) * 30)
                period_end = period_start + timedelta(days=30)
                issue = period_start
                due = issue + timedelta(days=14)

                subtotal = Decimal("250.00") * Decimal(1 + (i % 3))
                tax_amt = Decimal(round(float(subtotal) * 0.10, 2))
                total = subtotal + tax_amt

                if st == "PAID":
                    paid = total
                    due_amt = Decimal("0.00")
                elif st == "CONFIRMED" or st == "DRAFT":
                    paid = Decimal("0.00")
                    due_amt = total
                else:  # OVERDUE
                    paid = Decimal("0.00")
                    due_amt = total
                    due = today - timedelta(days=15)  # past due

                inv = Invoice(
                    id=inv_id,
                    organization_id=org_id,
                    customer_id=cust.id,
                    subscription_id=sub.id,
                    invoice_number=f"INV-2026-{i:06d}",
                    issue_date=issue,
                    due_date=due,
                    period_start=period_start,
                    period_end=period_end,
                    currency="USD",
                    subtotal=subtotal,
                    discount_total=Decimal("0.00"),
                    tax_total=tax_amt,
                    sla_credit_amount=Decimal("0.00"),
                    total_amount=total,
                    amount_paid=paid,
                    amount_due=due_amt,
                    status=st,
                    verification_status="VERIFIED",
                )
                new_invoices.append(inv)

                inv_item = InvoiceItem(
                    invoice_id=inv_id,
                    description=f"Enterprise Telemetry & Platform Access - Batch {i:04d}",
                    quantity=1 + (i % 3),
                    unit_price=Decimal("250.00"),
                    line_total=subtotal,
                )
                new_inv_items.append(inv_item)

            db.bulk_save_objects(new_invoices)
            db.bulk_save_objects(new_inv_items)
            db.commit()
            print("✓ 5,000 Invoices committed to database.")

        all_invoices = (
            db.query(Invoice)
            .filter(Invoice.organization_id == org_id)
            .limit(3000)
            .all()
        )

        # 8. Seed 3,000 Payments
        existing_pay_count = db.query(Payment).filter(Payment.organization_id == org_id).count()
        payments_to_create = 3000 - existing_pay_count

        if payments_to_create > 0:
            print(f"⏳ Generating {payments_to_create} Payment settlement transactions...")
            methods = ["SIMULATED", "CREDIT_CARD", "BANK_TRANSFER", "ACH", "SIMULATED"]
            new_payments = []
            for i in range(existing_pay_count, min(3000, len(all_invoices))):
                inv = all_invoices[i]
                pay = Payment(
                    organization_id=org_id,
                    invoice_id=inv.id,
                    amount=inv.total_amount,
                    payment_method=methods[i % len(methods)],
                    payment_date=datetime.now(timezone.utc) - timedelta(days=(i % 60)),
                    status="COMPLETED",
                    transaction_reference=f"PAY-TXN-{i:06d}",
                )
                new_payments.append(pay)

            db.bulk_save_objects(new_payments)
            db.commit()
            print("✓ 3,000 Payments committed to database.")

        # 9. Seed Initial SHA-256 Audit Chain
        existing_audit_count = db.query(AuditLog).filter(AuditLog.organization_id == org_id).count()
        if existing_audit_count < 10:
            print("⏳ Initializing SHA-256 Cryptographic Audit Hash-Chain...")
            audit_service = AuditService(db)
            audit_service.log_action(
                org_id=org_id,
                entity_type="SYSTEM",
                entity_id=str(org_id),
                action="INITIALIZE_PLATFORM_CLUSTER",
                actor_email=admin_user.email,
                payload={"message": "Platform seed initialization benchmark completed."},
            )
            print("✓ Cryptographic Audit Trail anchored to genesis block.")

        elapsed = time.time() - start_time
        print(f"\n✨ Performance Seed Complete in {elapsed:.2f} seconds!")
        print(f"   • Organization: 1")
        print(f"   • Users: 2")
        print(f"   • Customers: {db.query(Customer).filter(Customer.organization_id == org_id).count()}")
        print(f"   • Subscriptions: {db.query(Subscription).filter(Subscription.organization_id == org_id).count()}")
        print(f"   • Invoices: {db.query(Invoice).filter(Invoice.organization_id == org_id).count()}")
        print(f"   • Payments: {db.query(Payment).filter(Payment.organization_id == org_id).count()}")

    finally:
        db.close()


if __name__ == "__main__":
    seed_performance_data()
