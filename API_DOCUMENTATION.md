# VERISUB Subscription Engine API Reference

All endpoints are prefixed with `/api/v1/`.

---

## 1. Customer Management

### `POST /api/v1/customers`
Create a new customer within the organization.
- **Request Body**:
  ```json
  {
    "customer_code": "CUST-001",
    "company_name": "Infosys Technologies",
    "contact_name": "Aarav Sharma",
    "email": "aarav.sharma@infosys.com",
    "phone": "+91 9876543210",
    "billing_address": "Electronics City, Bengaluru, Karnataka",
    "tax_identifier": "29AABCU9603R1ZM",
    "status": "ACTIVE"
  }
  ```
- **Responses**:
  - `201 Created`: Returns created customer object.
  - `409 Conflict`: If `customer_code` or `email` already exists in this organization.

### `GET /api/v1/customers`
List and search customers with pagination and filtering.
- **Query Parameters**:
  - `search`: string (matches code, company, contact name, or email)
  - `status`: string (`ACTIVE`, `INACTIVE`, `SUSPENDED`)
  - `page`: int (default `1`)
  - `per_page`: int (default `20`, max `100`)

### `GET /api/v1/customers/{id}`
Retrieve customer details by UUID.

### `PATCH /api/v1/customers/{id}`
Update customer contact or billing fields.

### `DELETE /api/v1/customers/{id}`
Deactivates customer status to `INACTIVE`.

### `GET /api/v1/customers/{id}/invoices`
Returns actual billing invoices for this customer.

### `GET /api/v1/customers/{id}/subscriptions`
Returns all subscriptions belonging to this customer.

---

## 2. Product & Variant Management

### `POST /api/v1/products`
Create a product with optional initial variants. All prices use high-precision `Decimal`.
- **Request Body**:
  ```json
  {
    "name": "Odoo Enterprise",
    "product_type": "SAAS",
    "description": "Enterprise ERP solution",
    "sales_price": "1500.00",
    "cost_price": "800.00",
    "notes": "Available monthly and annually",
    "status": "ACTIVE",
    "variants": [
      {
        "variant_name": "Premium Support",
        "description": "24/7 dedicated telephone support",
        "additional_price": "560.00",
        "status": "ACTIVE"
      }
    ]
  }
  ```

### `GET /api/v1/products`
Search and filter products by `product_type`, `status`, and keyword.

### `GET /api/v1/products/{id}`
Get product details including attached variants.

### `PATCH /api/v1/products/{id}`
Update product fields or sales price.

### `DELETE /api/v1/products/{id}`
Archive product (`status="ARCHIVED"`).

### `POST /api/v1/products/{product_id}/variants`
Add a variant to a product.

### `GET /api/v1/products/{product_id}/variants`
List all variants for a given product.

### `PATCH /api/v1/variants/{id}`
Update variant name or `additional_price`.

### `DELETE /api/v1/variants/{id}`
Deactivate a variant.

---

## 3. Subscription Plan Management

### `POST /api/v1/plans`
Create a subscription plan with frequency and policy configurations.
- **Request Body**:
  ```json
  {
    "name": "Standard Enterprise Monthly",
    "description": "Monthly recurring SaaS plan",
    "billing_frequency": "MONTHLY",
    "plan_price": "2999.00",
    "minimum_quantity": 1,
    "start_availability_date": "2026-01-01",
    "end_availability_date": "2026-12-31",
    "auto_close_configuration": { "max_failed_payments": 3 },
    "early_closure_configuration": { "penalty_fee": "500.00" },
    "pause_configuration": { "max_pause_days": 60 },
    "renewal_configuration": { "auto_renew": true },
    "status": "ACTIVE"
  }
  ```
- Valid `billing_frequency` values: `DAILY`, `WEEKLY`, `MONTHLY`, `YEARLY`.

### `GET /api/v1/plans`
List plans with filtering by frequency and status.

### `GET /api/v1/plans/{id}`
Get plan details and policy configurations.

### `PATCH /api/v1/plans/{id}`
Update plan. If `plan_price` changes, an entry is automatically created in `plan_price_history`.

### `DELETE /api/v1/plans/{id}`
Archive plan (`status="ARCHIVED"`).

### `GET /api/v1/plans/{id}/price-history`
Get historical audit log of all price updates for the plan.

---

## 4. Quotation Management

### `POST /api/v1/quotations`
Create a draft quotation. Unit prices and descriptions are automatically snapshotted from catalog products and variants.
- **Request Body**:
  ```json
  {
    "customer_id": "...",
    "expiry_date": "2026-11-15",
    "discount_total": "500.00",
    "notes": "Custom introductory offer",
    "items": [
      {
        "product_id": "...",
        "variant_id": "...",
        "plan_id": "...",
        "quantity": 2,
        "tax_configuration_reference": "GST_18"
      }
    ]
  }
  ```

### `GET /api/v1/quotations`
List quotations filtered by `customer_id` and `status`.

### `GET /api/v1/quotations/{id}`
Get quotation details, line items, and totals.

### `PATCH /api/v1/quotations/{id}`
Update draft quotation items, expiry date, discount, and notes. Recalculates subtotal, taxes, and grand totals automatically.

### `POST /api/v1/quotations/{id}/confirm`
Confirm quotation (transitions from `DRAFT` to `CONFIRMED`). Fails if expiry date has passed.

### `POST /api/v1/quotations/{id}/cancel`
Cancel quotation (transitions to `CANCELLED`).

### `POST /api/v1/quotations/{id}/convert-to-subscription`
Converts confirmed quotation into an active/confirmed subscription. Locks item price snapshots and updates quotation status to `CONVERTED`.

---

## 5. Subscription Management & Lifecycle

### `POST /api/v1/subscriptions`
Directly create a subscription in `DRAFT`.
- Calculates `next_billing_date` according to `billing_frequency` (`DAILY`, `WEEKLY`, `MONTHLY`, `YEARLY`).
- Validates minimum quantity and plan availability.

### `GET /api/v1/subscriptions`
List subscriptions with filtering by customer, plan, status, and search by subscription number.

### `GET /api/v1/subscriptions/{id}`
Get subscription details, snapshot items, and schedule.

### `PATCH /api/v1/subscriptions/{id}`
Update metadata (payment terms, renewal flag).

### `POST /api/v1/subscriptions/{id}/activate`
Activates subscription (`CONFIRMED` or `DRAFT` -> `ACTIVE`). Establishes initial next billing schedule.

### `POST /api/v1/subscriptions/{id}/pause`
Pauses active subscription (`ACTIVE` -> `PAUSED`). Records `pause_information` (`reason`, `paused_at`, `resume_date`).

### `POST /api/v1/subscriptions/{id}/resume`
Resumes paused subscription (`PAUSED` -> `ACTIVE`). Logs resumption event in history.

### `POST /api/v1/subscriptions/{id}/renew`
Renews active subscription (`ACTIVE` -> `ACTIVE`). Advances `next_billing_date` and `expiry_date` by the specified periods.

### `POST /api/v1/subscriptions/{id}/close`
Closes subscription (`ACTIVE`/`PAUSED` -> `CLOSED`). Records `closure_information` (`reason`, `closed_at`, `early_closure_fee`).

### `GET /api/v1/subscriptions/{id}/events`
Returns chronological audit trail of all lifecycle events.

---

## 6. Subscription Digital Twin

### `GET /api/v1/subscriptions/{id}/digital-twin`
Returns a unified, real-time live view joining:
- Customer details (name, email, code, tax ID, billing address)
- Plan catalog state & availability
- Contractual recurring price and total value
- Frozen subscription items with snapshot unit prices
- Start date, next billing date, expiry date, billing frequency
- Linked quotations
- Real billing invoices and payment transactions
- Full subscription change event history
- Financial verification status

---

## 7. Change Impact Analysis

### `POST /api/v1/change-impact/product`
Previews the impact of a proposed product price change or deactivation without altering existing contracts:
- Reports affected active subscriptions
- Displays protected contractual recurring revenue
- Identifies pending quotations
- Guarantees existing customer contracts retain their agreed snapshot price

### `POST /api/v1/change-impact/plan`
Previews the impact of a proposed plan price or status change without modifying existing subscriptions.


---

## 8. Tax Engine

### `POST /api/v1/tax-rules`
Create a jurisdiction-specific tax rule (Admin only).
- **Request Body**:
  ```json
  {
    "name": "GST 18%",
    "tax_rate": "0.1800",
    "tax_type": "GST",
    "inclusive_or_exclusive": "EXCLUSIVE",
    "effective_from": "2026-10-31",
    "active": true
  }
  ```

### `GET /api/v1/tax-rules`
List configurable tax rules with optional `active_only=true` filter.

### `PATCH /api/v1/tax-rules/{id}`
Update tax rate, validity dates, or status.

---

## 9. Discount Engine

### `POST /api/v1/discounts`
Create commercial or promotional discounts (Admin only).
- **Request Body**:
  ```json
  {
    "discount_name": "Quarterly Incentive 10%",
    "discount_code": "Q4INCENTIVE",
    "discount_type": "PERCENTAGE",
    "discount_value": "10.00",
    "minimum_purchase": "1000.00",
    "minimum_quantity": 1,
    "start_date": "2026-10-01",
    "end_date": "2026-12-31",
    "usage_limit": 50,
    "subscription_wide": true,
    "active": true
  }
  ```

### `GET /api/v1/discounts`
List discounts for the active organization.

### `PATCH /api/v1/discounts/{id}`
Update discount parameters.

### `POST /api/v1/discounts/{id}/validate`
Evaluate real-time eligibility against cart/subtotal, item quantities, and usage limits.

---

## 10. Invoice Management

### `GET /api/v1/invoices`
List invoices with multi-tenant filtering, search query, status, and pagination.

### `POST /api/v1/invoices`
Generate one-time or recurring invoice with frozen item snapshots:
- Computes deterministic subtotal, discounts, and itemized tax breakdowns.

### `GET /api/v1/invoices/{id}`
Retrieve complete invoice details including line items and payment allocations.

### `POST /api/v1/invoices/{id}/confirm`
Transition `DRAFT` invoice to `CONFIRMED`, locking financial values against unauthorized edits.

### `POST /api/v1/invoices/{id}/cancel`
Cancel an unpaid invoice with mandatory audit explanation.

### `PATCH /api/v1/invoices/{id}/status`
Update status (`DRAFT`, `CONFIRMED`, `PARTIALLY_PAID`, `PAID`, `OVERDUE`, `CANCELLED`).

### `GET /api/v1/invoices/{id}/pdf`
Download a print-ready, formatted PDF tax invoice generated via ReportLab.

---

## 11. Recurring Billing Engine

### `POST /api/v1/billing/run` (alias `POST /api/v1/billing/execute`)
Execute on-demand or automated recurring billing run:
- Finds active due subscriptions (`next_billing_date <= as_of_date`).
- Respects `PAUSED`, `CLOSED`, `CANCELLED`, and `EXPIRED` subscriptions.
- Enforces database-level uniqueness constraint preventing duplicate invoices per billing period.
- Advances `next_billing_date` only after successful processing.
- Records `BillingRun` and itemized `BillingRunItem` execution history.

### `GET /api/v1/billing/runs`
List recurring billing execution history.

### `GET /api/v1/billing/runs/{id}`
Inspect itemized execution log and failure reasons.

### `GET /api/v1/billing/due-subscriptions`
Preview billable subscriptions due on or before specified target date.

---

## 12. Payment Management & Allocations

### `POST /api/v1/payments`
Record payment receipt with method (`BANK_TRANSFER`, `CASH`, `CARD`, `UPI`, `OTHER`).
- Supports direct invoice allocation or unallocated customer balance.

### `GET /api/v1/payments`
List recorded payments.

### `GET /api/v1/payments/{id}`
Retrieve payment details and allocations.

### `POST /api/v1/payments/{id}/allocate`
Allocate payment funds to one or more invoices. Enforces payment balance and invoice balance caps.

### `POST /api/v1/payments/{id}/refund`
Record full or partial refund against a payment.

### `GET /api/v1/invoices/{id}/payments`
Retrieve all payments and allocations settled against an invoice.

---

## 13. Payment Reconciliation

### `POST /api/v1/reconciliation/import` (alias `POST /api/v1/payments/reconcile-csv`)
Import bank statement CSV (`transaction_date, reference, description, amount, currency`):
- Deterministic multi-rule matching.
- Outputs `MATCHED`, `POTENTIAL_DUPLICATE`, `AMOUNT_MISMATCH`, and `NEEDS_MANUAL_REVIEW`.

### `GET /api/v1/reconciliation/runs`
List statement reconciliation runs.

### `POST /api/v1/reconciliation/{id}/review` (alias `POST /api/v1/payments/reconcile/match`)
Manually review or bind an unmatched transaction to an invoice.

---

## 14. Contract-to-Bill / Value Verification

### `POST /api/v1/verification/contracts`
Define contractual SLA commitments for a subscription (`UPTIME`, `RESPONSE_TIME`, `DELIVERED_HOURS`, `penalty_rate_per_unit`).

### `POST /api/v1/verification/events`
Record verified service delivery telemetry events from monitoring systems or evidence references.

### `POST /api/v1/verification/run/{subscription_id}`
Compare contracted commitments against verified service events:
- Calculates exact variance.
- Formulates plain-English discrepancy explanations citing real evidence references.
- Proposes SLA service credit when penalty rate is configured.

### `GET /api/v1/verification/{subscription_id}`
List historical verification runs and overall results (`COMPLIANT`, `BREACH`, `PARTIAL_BREACH`).

### `POST /api/v1/verification/credits/{id}/approve`
Authorized managerial approval of proposed SLA service credit.

### `POST /api/v1/verification/credits/{id}/reject`
Reject proposed service credit with reason.

---

## 15. AI Invoice Anomaly Detection & Business Assistant

### `POST /api/v1/ai/anomalies/detect`
Run deterministic and statistical anomaly detection across invoices:
- Flags duplicate invoices, excessive discounts (> 50%), unusual tax ratios, recurring charge jumps, and overpayments.
- Formulates plain-English database difference explanations.

### `GET /api/v1/ai/anomalies` (alias `GET /api/v1/ai/insights`)
List active financial risk signals.

### `POST /api/v1/ai/anomalies/{id}/review`
Mark an anomaly as reviewed or false positive.

### `POST /api/v1/ai/assistant/query` (alias `POST /api/v1/ai/assistant/chat`)
Natural language assistant answering live ledger queries:
- Outstanding amount
- Overdue invoices
- Unusual billing / anomalies
- Customers with unpaid invoices
- SLA commitments not met

---

## 16. Tamper-Evident Audit & Blockchain Anchoring

### `GET /api/v1/audit/events` (alias `GET /api/v1/audit-logs`)
Chronological audit ledger with actor, action, timestamp, change summary, and cryptographic SHA-256 block hashes.

### `GET /api/v1/audit/verify` (alias `POST /api/v1/audit-logs/verify-integrity`)
Verify cryptographic integrity of the SHA-256 hash chain from genesis to head.

### `POST /api/v1/audit/anchor`
Anchor the latest audit root hash to an Ethereum test network (Sepolia).
