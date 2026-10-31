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
