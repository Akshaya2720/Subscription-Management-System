# Pull Request: Feature - Billing, Financial Verification, AI and Blockchain Layer

- **Base branch**: `develop`
- **Compare branch**: `feature/billing-verification`
- **PR URL**: [Create Pull Request on GitHub](https://github.com/Akshaya2720/Subscription-Management-System/compare/develop...feature/billing-verification?expand=1)

---

## 1. Features Completed

### 1. Recurring Billing Engine (`app/modules/billing/recurring.py`)
- Automated recurring billing execution with batch run tracking (`BillingRun` & `BillingRunItem`).
- Support for `DAILY`, `WEEKLY`, `MONTHLY`, and `YEARLY` billing frequencies.
- Selection of due subscriptions (`next_billing_date <= as_of_date` and `status == "ACTIVE"`).
- Safe skipping of paused, closed, cancelled, expired, and not-yet-due subscriptions.
- Database-level unique constraint (`uq_invoice_sub_period_type`) preventing duplicate recurring invoices for the same period.
- Transactional integrity: advances `next_billing_date` only upon successful invoice creation.

### 2. Invoice Management (`app/modules/billing/invoices.py`)
- Full invoice state machine: `Draft` -> `Confirmed` -> `Paid` / `Partially Paid` / `Overdue` / `Cancelled` / `Voided`.
- Immutable pricing snapshots (`description_snapshot`, `unit_price`, `quantity`, `discount_amount`, `tax_amount`, `line_total`).
- Prevention of modification of confirmed financial values without authorized adjustment.
- Sequential unique invoice numbering per organization (`INV-YYYY-XXXX`).
- Print-ready PDF invoice generation using ReportLab.

### 3. Tax Engine (`app/modules/billing/taxes.py`)
- Configurable jurisdiction-specific tax rules (`TaxRule`: name, rate, type, inclusive/exclusive, validity dates).
- High-precision Decimal arithmetic with `ROUND_HALF_UP` to prevent floating-point errors.
- Support for multiple active tax rules, tax-inclusive calculations, and tax-exclusive calculations.
- Itemized tax breakdown output on invoices.

### 4. Discount Engine (`app/modules/billing/discounts.py`)
- Fixed amount and percentage discount types.
- Strict validation of date windows, minimum purchase amount, minimum item quantity, and usage limits.
- Concurrency-safe row locking (`with_for_update`) to prevent discount overuse during concurrent checkout requests.
- Audit trail for redemptions in `discount_redemptions`.
- Automatic proportional application to eligible invoices.

### 5. Payment Management & Allocations (`app/modules/billing/payments.py`)
- Multi-method recording: Bank Transfer, Card, Cash, UPI, and configurable alternatives.
- Multi-invoice payment allocation (`PaymentAllocation` connecting one payment to one or more invoices).
- Support for full payment, partial payment, multiple payments per invoice, and overpayment handling.
- Full and partial refund tracking in `payment_refunds`.
- Automatic invoice balance and status updates (`PAID` only when amount_paid covers total_amount).

### 6. Payment Reconciliation (`app/modules/billing/reconciliation.py`)
- CSV bank statement parser supporting transaction date, reference, description, amount, and currency.
- Multi-rule deterministic matching engine classifying transactions as:
  - `MATCHED` (exact reference & amount match)
  - `POTENTIAL_DUPLICATE` (duplicate statement references)
  - `AMOUNT_MISMATCH` (reference match with divergent amount)
  - `NEEDS_MANUAL_REVIEW` (ambiguous date/amount match)
  - `UNMATCHED`
- Interactive manual review and matching workflow.

### 7. Contract-to-Bill / Value Verification (`app/modules/billing/verification.py`)
- Differentiating capability: compares contractual commitments (`ServiceCommitment`) with verified delivery telemetry (`ServiceEvent`).
- Deterministic verification rules: `GREATER_OR_EQUAL`, `LESS_OR_EQUAL`, `EXACT`.
- Generates plain-English discrepancy explanations citing actual database evidence references (e.g. Datadog/CloudWatch incidents).
- Automatic calculation of proposed service credits (`variance * penalty_rate_per_unit`).
- Managerial Approve/Reject workflow (`ServiceCredit`) before financial adjustment.

### 8. Explainable AI Invoice Anomaly Detection & Business Assistant (`app/modules/billing/anomaly.py` & `assistant.py`)
- Deterministic explainable rules: duplicate invoices, unusual amounts, unexpected price changes, incorrect tax calculations, unusual discounts (> 50%), charge jumps (> 40%), overpayment mismatches.
- Scikit-learn `IsolationForest` integration when historical clusters exist (>= 5 invoices).
- Plain-English database difference explanations.
- Controlled natural language assistant querying live database ledger without arbitrary SQL execution.

### 9. Tamper-Evident SHA-256 Audit Trail & Blockchain Anchoring (`app/modules/billing/audit.py`)
- SHA-256 cryptographic hash-chained audit ledger.
- Canonical block hashing: `previous_hash|org_id|actor_id|action|entity_type|entity_id|timestamp|change_summary`.
- Integrity verification endpoint checking the hash chain from genesis to head.
- Verifiable blockchain anchoring to Ethereum Sepolia testnet recording transaction hash and block state root.

---

## 2. API Endpoints Added

Prefix: `/api/v1/`

### Taxes
- `POST /api/v1/tax-rules`
- `GET /api/v1/tax-rules`
- `PATCH /api/v1/tax-rules/{id}`

### Discounts
- `POST /api/v1/discounts`
- `GET /api/v1/discounts`
- `PATCH /api/v1/discounts/{id}`
- `POST /api/v1/discounts/{id}/validate`

### Invoices
- `GET /api/v1/invoices`
- `POST /api/v1/invoices`
- `GET /api/v1/invoices/{id}`
- `POST /api/v1/invoices/{id}/confirm`
- `POST /api/v1/invoices/{id}/cancel`
- `PATCH /api/v1/invoices/{id}/status`
- `GET /api/v1/invoices/{id}/pdf`

### Recurring Billing
- `POST /api/v1/billing/run` (alias `POST /api/v1/billing/execute`)
- `GET /api/v1/billing/runs`
- `GET /api/v1/billing/runs/{id}`
- `GET /api/v1/billing/due-subscriptions`

### Payments
- `POST /api/v1/payments`
- `GET /api/v1/payments`
- `GET /api/v1/payments/{id}`
- `POST /api/v1/payments/{id}/allocate`
- `POST /api/v1/payments/{id}/refund`
- `GET /api/v1/invoices/{id}/payments`

### Reconciliation
- `POST /api/v1/reconciliation/import` (alias `POST /api/v1/payments/reconcile-csv`)
- `GET /api/v1/reconciliation/runs` (alias `GET /api/v1/payments/reconciliation`)
- `POST /api/v1/reconciliation/{id}/review` (alias `POST /api/v1/payments/reconcile/match`)

### Value Verification
- `POST /api/v1/verification/contracts`
- `GET /api/v1/verification/contracts`
- `POST /api/v1/verification/events`
- `POST /api/v1/verification/run/{subscription_id}`
- `GET /api/v1/verification/{subscription_id}`
- `GET /api/v1/verification/results/{id}`
- `POST /api/v1/verification/credits/{id}/approve`
- `POST /api/v1/verification/credits/{id}/reject`

### AI & Assistant
- `POST /api/v1/ai/anomalies/detect`
- `GET /api/v1/ai/anomalies` (alias `GET /api/v1/ai/insights`)
- `POST /api/v1/ai/anomalies/{id}/review` (alias `POST /api/v1/ai/insights/{id}/acknowledge`)
- `POST /api/v1/ai/assistant/query` (alias `POST /api/v1/ai/assistant/chat`)

### Audit & Blockchain
- `GET /api/v1/audit/events` (alias `GET /api/v1/audit-logs`)
- `GET /api/v1/audit/verify` (alias `POST /api/v1/audit-logs/verify-integrity`)
- `POST /api/v1/audit/anchor`

---

## 3. Financial Calculation Rules & Guarantees
1. **Precision Arithmetic**: Python `Decimal` with SQL `Numeric(14, 2)` or `Numeric(14, 4)` is strictly enforced for all currency and percentage arithmetic. Floating-point arithmetic is never used.
2. **Rounding Convention**: `ROUND_HALF_UP` is applied deterministically on line-item taxes, discounts, and totals.
3. **Immutability Guarantee**: Once an invoice is confirmed (`CONFIRMED`), its unit prices, descriptions, and line totals cannot be mutated. Financial changes must be executed via auditable credit notes, refunds, or service credit adjustments.
4. **Payment Sufficiency**: An invoice status is updated to `PAID` if and only if the cumulative allocated payments equal or exceed the grand total.
5. **Multi-Tenancy Guarantee**: Every query filters by `organization_id`, strictly preventing cross-tenant leakage.

---

## 4. AI & Blockchain Limitations
- **AI Disclosures**: AI and machine learning tools function strictly as advisory signals. Anomaly detection flags statistical or rule-based outliers for human review. AI models never autonomously alter invoice totals, tax rates, payment allocations, or approved service credits.
- **Blockchain Disclosures**: The primary tamper-evidence guarantee is provided by local SHA-256 hash chaining. Optional blockchain testnet anchoring commits only the root block hash; private financial data, customer identities, and invoices are never stored on-chain.
- **Payment Gateway Disclosure**: To preserve deterministic auditability without simulating false gateway authorizations, payment recording operates through an explicitly labeled manual recording workflow.

---

## 5. Verification & Testing Results

- **Backend Pytest**: **29/29 tests passed (100%) in 2.28s**.
- **Frontend Vitest**: **15/15 tests passed (100%) in 4.01s**.
- **Database Migrations**: Alembic migration `2f5d3c1003d4` successfully created and tested.

---

# Previous Pull Request Documentation: Subscription Engine

# Pull Request: Feature - Complete Subscription Engine Lifecycle

- **Base branch**: `develop`
- **Compare branch**: `feature/subscription-engine`
- **PR URL**: [Create Pull Request on GitHub](https://github.com/Akshaya2720/Subscription-Management-System/compare/develop...feature/subscription-engine?expand=1)

---

## 1. Features Completed

1. **Customer Management**:
   - Customer CRUD, search (multi-field matching), status filtering, and pagination.
   - Multi-tenant unique constraints (`organization_id` + `customer_code`, `organization_id` + `email`).
   - Customer subscription history and billing invoice history integration.

2. **Product & Product Variant Management**:
   - Product CRUD with high-precision `Decimal` financial pricing.
   - Variant CRUD with additive pricing (e.g. ₹560 for Premium Support).
   - Search, filtering, and deactivation/archival.

3. **Subscription Plan Management**:
   - Plan configuration supporting `DAILY`, `WEEKLY`, `MONTHLY`, and `YEARLY` billing intervals.
   - Policy JSON configurations (`auto_close_configuration`, `early_closure_configuration`, `pause_configuration`, `renewal_configuration`).
   - Availability window validation (`start_availability_date` and `end_availability_date`).
   - Immutable price history tracking (`plan_price_history`) preventing retroactive modification of existing subscriptions.

4. **Quotation Workflow**:
   - Quotation creation with immutable product/variant pricing snapshots.
   - Integration with Member 3's financial contract (`TaxDiscountServiceInterface`) calculating subtotals, discounts, tax brackets (e.g. GST 18%), and grand totals.
   - Lifecycle state machine: `DRAFT` → `CONFIRMED` → `CONVERTED` / `CANCELLED`.
   - Expiry date validation preventing confirmation or conversion of expired quotations.
   - Automated conversion into subscriptions preserving agreed pricing snapshots.

5. **Subscription Lifecycle Engine**:
   - State machine enforcing valid transitions (`DRAFT` / `CONFIRMED` → `ACTIVE` → `PAUSED` → `ACTIVE` → `CLOSED`).
   - Blocking illegal transitions (activating expired subscriptions, resuming unpaused subscriptions, etc.).
   - Billing cycle calculators for next billing dates and period renewals.
   - Pause with reason and resume date tracking; resume with audit logging; renewal with extension periods; closure with early closure fee.
   - Comprehensive audit event logging (`subscription_events`).

6. **Subscription Digital Twin**:
   - Live query combining real database records for customer, plan, pricing snapshots, subscription items, quotations, invoices, payments, and audit events.
   - Zero mock data.

7. **Change Impact Analysis**:
   - Previews the effect of proposed product or plan revisions (price changes, deactivations) on active subscriptions, protected revenue, and pending quotations.
   - Guarantees: *"Existing customer subscriptions retain their agreed contractual snapshot price."*

---

## 2. API Endpoints Added

Prefix: `/api/v1/`

### Customers
- `POST /api/v1/customers`
- `GET /api/v1/customers`
- `GET /api/v1/customers/{id}`
- `PATCH /api/v1/customers/{id}`
- `DELETE /api/v1/customers/{id}`
- `GET /api/v1/customers/{id}/subscriptions`
- `GET /api/v1/customers/{id}/invoices`

### Products & Variants
- `POST /api/v1/products`
- `GET /api/v1/products`
- `GET /api/v1/products/{id}`
- `PATCH /api/v1/products/{id}`
- `DELETE /api/v1/products/{id}`
- `POST /api/v1/products/{product_id}/variants`
- `GET /api/v1/products/{product_id}/variants`
- `PATCH /api/v1/variants/{id}`
- `DELETE /api/v1/variants/{id}`

### Subscription Plans
- `POST /api/v1/plans`
- `GET /api/v1/plans`
- `GET /api/v1/plans/{id}`
- `PATCH /api/v1/plans/{id}`
- `DELETE /api/v1/plans/{id}`
- `GET /api/v1/plans/{id}/price-history`

### Quotations
- `POST /api/v1/quotations`
- `GET /api/v1/quotations`
- `GET /api/v1/quotations/{id}`
- `PATCH /api/v1/quotations/{id}`
- `POST /api/v1/quotations/{id}/confirm`
- `POST /api/v1/quotations/{id}/cancel`
- `POST /api/v1/quotations/{id}/convert-to-subscription`

### Subscriptions & Digital Twin
- `POST /api/v1/subscriptions`
- `GET /api/v1/subscriptions`
- `GET /api/v1/subscriptions/{id}`
- `PATCH /api/v1/subscriptions/{id}`
- `POST /api/v1/subscriptions/{id}/activate`
- `POST /api/v1/subscriptions/{id}/pause`
- `POST /api/v1/subscriptions/{id}/resume`
- `POST /api/v1/subscriptions/{id}/renew`
- `POST /api/v1/subscriptions/{id}/close`
- `GET /api/v1/subscriptions/{id}/digital-twin`
- `GET /api/v1/subscriptions/{id}/events`

### Change Impact Analysis
- `POST /api/v1/change-impact/product`
- `POST /api/v1/change-impact/plan`

---

## 3. Database Changes

Alembic migration: `127056ed81a1_initial_subscription_engine_tables.py`
Tables created:
1. `organizations` (UUID PK, slug, active status)
2. `users` (UUID PK, organization_id FK, email, role)
3. `customers` (UUID PK, organization_id FK, customer_code, contact_name, email, unique constraints)
4. `products` (UUID PK, organization_id FK, sales_price Numeric(14, 2))
5. `product_variants` (UUID PK, product_id FK, additional_price Numeric(14, 2))
6. `subscription_plans` (UUID PK, organization_id FK, plan_price Numeric(14, 2), billing_frequency)
7. `plan_price_history` (UUID PK, plan_id FK, price Numeric(14, 2), effective_from)
8. `quotations` (UUID PK, organization_id FK, customer_id FK, subtotal, discount, tax, grand_total Numeric(14, 2))
9. `quotation_items` (UUID PK, quotation_id FK, product_id FK, variant_id FK, unit_price Numeric(14, 2))
10. `subscriptions` (UUID PK, organization_id FK, customer_id FK, plan_id FK, quotation_id FK, start_date, next_billing_date)
11. `subscription_items` (UUID PK, subscription_id FK, unit_price_snapshot Numeric(14, 2), line_total Numeric(14, 2))
12. `subscription_events` (UUID PK, subscription_id FK, event_type, metadata_json)
13. `invoices` (UUID PK, organization_id FK, customer_id FK, subscription_id FK, status, verification_status)
14. `payments` (UUID PK, organization_id FK, invoice_id FK, amount Numeric(14, 2), status)

---

## 4. Tests Performed

Automated test suite (`pytest -v`):
- **19 passed** in 1.02s
- Customer CRUD, duplicate handling, search, filter, pagination
- Product & variant CRUD, variant additive pricing, Decimal arithmetic
- Plan availability, frequency validation, price history audit log
- Quotation workflow, tax calculation, expiry check, conversion to subscription
- Subscription lifecycle state machine (Draft → Active → Pause → Resume → Renew → Close)
- Digital Twin database accuracy
- Change impact preview reports
- Cross-organization tenant isolation

---

## 5. Known Limitations

- Multi-currency conversions currently use static currency snapshots (`INR`, `USD`). Dynamic FX rate lookups can be hooked in future iterations.
- Member 3 billing interface supports GST 18%, 12%, 5%, and VAT 20%; additional regional tax jurisdictions can be added via Member 3's tax provider hook.
