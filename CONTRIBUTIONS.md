# CONTRIBUTIONS.md - VERISUB Platform Contributions

This document aggregates engineering contributions across the VERISUB Intelligent Subscription & Billing Verification Platform.

---

# Part 1: Member 3 — Billing, Financial Verification, AI and Blockchain Developer
**Role**: Billing, Financial Verification, AI and Blockchain Developer  
**Assigned Branch**: `feature/billing-verification`  
**Target Branch for PR**: `develop`

## 1. Summary of Delivered Work
As the Billing, Financial Verification, AI and Blockchain Developer (Member 3), I am responsible for the financial processing and intelligent verification layer of VERISUB. All financial calculations use deterministic Decimal arithmetic (`Numeric(14, 2)`), database-level uniqueness constraints, and strict organization-level multi-tenant isolation.

Delivered capabilities:
- **Recurring Billing Engine (`app/modules/billing/recurring.py`)**:
  - Automated recurring billing execution with batch runs (`BillingRun` & `BillingRunItem`).
  - Supports `DAILY`, `WEEKLY`, `MONTHLY`, and `YEARLY` cadences.
  - Due subscription selection respecting active status, `next_billing_date`, and expiry date.
  - Explicitly bypasses paused, closed, cancelled, expired, or future subscriptions.
  - Enforces database-level unique constraint (`uq_invoice_sub_period_type`) preventing duplicate invoices for the same subscription, billing period, and invoice type.
  - Updates `next_billing_date` only after successful transaction commit.
- **Invoice Management (`app/modules/billing/invoices.py`)**:
  - Full lifecycle state machine: `Draft` -> `Confirmed` -> `Paid` / `Partially Paid` / `Overdue` / `Cancelled` / `Voided`.
  - Immutable price snapshots and description snapshots preserved in `invoice_items`.
  - Sequential unique invoice numbering per organization (`INV-YYYY-XXXX`).
  - Print-ready PDF invoice generation via ReportLab with complete itemization, tax breakdown, and payment status.
- **Tax Engine (`app/modules/billing/taxes.py`)**:
  - Configurable organization-specific tax rules (`TaxRule`: name, rate, type, inclusive/exclusive, validity dates).
  - High-precision Decimal arithmetic with `ROUND_HALF_UP` to prevent floating-point discrepancies.
  - Supports both tax-inclusive and tax-exclusive calculations with full itemized breakdown.
- **Discount Engine (`app/modules/billing/discounts.py`)**:
  - Fixed amount and percentage discounts.
  - Validates date ranges, minimum purchase threshold, minimum item quantity, and usage limits.
  - Concurrency-safe row locking (`with_for_update`) to prevent discount overuse during concurrent checkout requests.
  - Detailed redemption tracking in `discount_redemptions`.
- **Payment Management & Allocations (`app/modules/billing/payments.py`)**:
  - Multi-method recording: Bank Transfer, Card, Cash, UPI, and configurable alternatives.
  - Connects one payment with one or more invoices via `PaymentAllocation`.
  - Automatic balance calculation (`amount_due = total_amount - amount_paid`).
  - Overpayment handling and full/partial refund tracking (`PaymentRefund`).
  - Invoice status auto-updated to `PAID` only when allocated payments completely satisfy the grand total.
- **Payment Reconciliation (`app/modules/billing/reconciliation.py`)**:
  - CSV bank statement parser supporting standard bank exports.
  - Deterministic matching rules classifying entries as: `MATCHED`, `UNMATCHED`, `POTENTIAL_DUPLICATE`, `AMOUNT_MISMATCH`, and `NEEDS_MANUAL_REVIEW`.
  - Interactive manual review workflow for unmatched transactions.
- **Contract-to-Bill / Value Verification (`app/modules/billing/verification.py`)**:
  - Core differentiating capability of VERISUB: compares contractual SLA commitments against actual service delivery telemetry.
  - Data models: `Contract`, `ServiceCommitment`, `ServiceEvent`, `VerificationRun`, `VerificationResult`, `ServiceCredit`.
  - Rules: `GREATER_OR_EQUAL`, `LESS_OR_EQUAL`, `EXACT`.
  - Generates plain-English discrepancy explanations referencing real database evidence (e.g., Datadog/CloudWatch incidents).
  - Computes proposed service credits and requires authorized human manager approval before financial application.
- **AI Invoice Anomaly Detection (`app/modules/billing/anomaly.py`)**:
  - Explainable deterministic rules: duplicate invoice detection, excessive discounts (> 50%), abnormal tax ratios, sudden charge jumps (> 40%), and overpayment mismatches.
  - Plain-English database difference summaries explaining why values shifted.
  - Scikit-learn `IsolationForest` integration when historical clusters exist (>= 5 invoices), with clear documentation of model limits.
- **Explainable Business Assistant (`app/modules/billing/assistant.py`)**:
  - Controlled conversational query engine answering questions about outstanding balances, overdue invoices, unusual charges, unpaid customers, and SLA breaches.
  - Queries live database models with strict organization-level isolation; no arbitrary SQL execution.
- **Tamper-Evident Audit & Blockchain Anchoring (`app/modules/billing/audit.py`)**:
  - SHA-256 cryptographic hash-chained audit ledger.
  - Canonical deterministic block serialization hashing `previous_hash|org_id|actor_id|action|entity_type|entity_id|timestamp|change_summary`.
  - Chain integrity verification endpoint detecting any mutation or broken link.
  - Verifiable blockchain anchoring to Ethereum Sepolia testnet recording transaction hash and block state root.

## 2. Test Verification & Results
All 29 backend tests and 15 frontend tests pass with 100% success:

### Backend Test Suite:
```bash
.venv/Scripts/python.exe -m pytest -v
```
**Results: 29 passed in 2.28s**:
- `tests/test_taxes_discounts.py`: Tax rules (inclusive/exclusive/breakdown), discounts (expiry, usage limits, minimum purchase/quantity, redemptions).
- `tests/test_invoices_recurring.py`: Due subscription selection, daily/weekly/monthly/yearly period calculations, duplicate invoice prevention, paused/closed/cancelled skipping, invoice PDF generation.
- `tests/test_payments_reconciliation.py`: Manual payments, multi-invoice allocations, partial payments, overpayments, refunds, CSV bank reconciliation (exact match, potential duplicate, amount mismatch, manual review).
- `tests/test_verification_audit_ai.py`: Contract SLA commitments, telemetry service events, verification runs, variance analysis, service credit approval/rejection, AI anomaly detection (tax, discount, duplicate, sudden increase, payment mismatch), explainable business assistant queries, SHA-256 hash-chain audit integrity verification, and multi-tenant organization isolation.
- `tests/test_customers.py`, `tests/test_products_variants.py`, `tests/test_plans.py`, `tests/test_quotations.py`, `tests/test_subscriptions.py`, `tests/test_digital_twin.py`, `tests/test_impact_analysis.py`, `tests/test_organization_isolation.py`: All 19 existing tests pass without regressions.

### Frontend Test Suite:
```bash
npm --prefix frontend run test -- --run
```
**Results: 6 test files passed, 15/15 tests passed (100%)**.

## 3. Database Migrations
- Migration `2f5d3c1003d4_add_billing_verification_tables.py` added to Alembic tracking revision `127056ed81a1 -> 2f5d3c1003d4`.
- Added 18 new tables and indexes: `invoice_items`, `billing_runs`, `billing_run_items`, `tax_rules`, `discounts`, `discount_redemptions`, `payment_allocations`, `payment_refunds`, `reconciliation_runs`, `reconciliation_items`, `contracts`, `service_commitments`, `service_events`, `verification_runs`, `verification_results`, `service_credits`, `invoice_anomalies`, `audit_events`.
- Enforces composite unique constraint `uq_invoice_sub_period_type` on `invoices`.

## 4. Disclosures & System Limits
- **AI Anomaly Detection**: Deterministic rules provide guaranteed explanations based on database diffs. Machine learning (IsolationForest) operates only as an advisory signal when >= 5 historical records exist and never independently modifies financial ledgers or authoritative charges.
- **Blockchain Anchoring**: Testnet anchoring publishes only the SHA-256 state root hash to the network; private business metrics and customer data are never written on-chain. Local SHA-256 hash chaining operates independently without requiring an active external web3 network.
- **Payment Processing**: Gateway integration provides an explicitly labeled manual payment recording workflow to maintain auditability without simulating false gateway authorizations.

---

# Part 2: Member 2 — Subscription Engine
**Role**: Subscription Engine Backend Developer  
**Assigned Branch**: `feature/subscription-engine`  
**Target Branch for PR**: `develop`

## Summary of Delivered Work
- **Core Models & Database Foundation**: Customer, Product, Product Variant, Subscription Plan, Quotation, Subscription models.
- **Subscription Lifecycle Management**: State machine (`DRAFT`, `CONFIRMED`, `ACTIVE`, `PAUSED`, `CLOSED`), billing frequency cadence, event audit logging.
- **Subscription Digital Twin**: Telemetry snapshot aggregating customer profile, line items, plan terms, quotations, billing history, and verification metrics.
- **Change Impact Analysis**: Impact preview on revenue and active subscribers when catalog items are revised.
- **Quotation Workflow**: Quotation lifecycle and deterministic conversion to active subscriptions.

---

# Part 3: Member 4 — Frontend Architect and UI/UX Developer
**Role**: Frontend Architect and UI/UX Developer  
**Branch**: `feature/frontend-dashboard`  
**Target Pull Request Base**: `develop`

## Summary of Delivered Work
- **Framework & Styling**: React 18 + TypeScript + Vite + Tailwind CSS.
- **Admin & Staff Dashboards**: MRR analytics, subscription velocity, billing inflow, and invoice health distribution.
- **Interactive Modules**: Customer management, products/plans, quotations, subscriptions, billing runs, invoices, payments, CSV bank reconciliation, contract verification, AI insights copilot, and audit trail.
- **Customer Portal**: Self-service subscription overview, invoices, payments, SLA compliance meters, and dispute workflows.
