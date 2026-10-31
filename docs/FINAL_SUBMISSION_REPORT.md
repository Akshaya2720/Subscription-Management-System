# VERISUB — Intelligent Subscription & Billing Verification Platform
## Final Hackathon Submission & Technical Defense Report

---

### 1. Executive Summary
**VERISUB** is an enterprise-grade subscription management and automated contract-to-bill verification platform built for high-scale B2B SaaS businesses. 

The system implements the full subscription lifecycle:
1. **Catalog & Frozen Pricing Snapshots**: Products with additive variant deltas (e.g. `+ ₹560.00 Odoo Brand`) and configurable policy plans (pausable, renewable, early closure, auto-close).
2. **Quotation Workflow**: Converts frozen quotation line items into subscriptions while preserving agreed contractual rates.
3. **Subscription Lifecycle & Digital Twin**: Authoritative state machine (`DRAFT` → `CONFIRMED` → `ACTIVE` ↔ `PAUSED` → `CLOSED`) maintaining a unified Digital Twin of contract terms, telemetry, event logs, and billing history.
4. **Automated Recurring Billing Run**: Idempotent billing runs with database-enforced non-overlapping uniqueness constraints (`subscription_id, period_start, period_end`), automated tax and discount calculation, and printable itemized tax invoices.
5. **Contract-to-Bill Value Verification**: Automatically correlates live service telemetry against contracted SLA uptime commitments and calculates automated service credits upon breach.
6. **Settlement & Audit**: Simulated payment gateway settlement linked to invoices, backed by a tamper-evident **SHA-256 cryptographic hash-chain audit ledger**.

---

### 2. High-Volume Performance Benchmark Results
Tested against **1 Organization, 2 Users, 500 Customers, 1,000 Subscriptions, 5,000 Invoices, and 3,000 Payments**:

| Benchmark Query / Flow | Target Requirement | Measured Latency | Verification Method |
| :--- | :--- | :--- | :--- |
| **Finance Executive Dashboard** | $< 2,000$ ms | **94.15 ms** | Single-pass SQL aggregation (`func.count`, `func.sum`) |
| **Invoice Pagination (Page 1)** | $< 2,000$ ms | **20.48 ms** | Eager loading (`selectinload(Invoice.items)`) |
| **Invoice Pagination (Page 20, Offset 1000)** | $< 2,000$ ms | **15.62 ms** | Composite index (`ix_invoices_org_status_due`) |
| **Active Subscription Search** | $< 2,000$ ms | **15.46 ms** | Multi-column index (`ix_subscriptions_org_status`) |
| **Index Usage Verification** | 100% Index Coverage | **Verified** | `EXPLAIN QUERY PLAN` SQLite & Postgres |
| **Brute-Force Rate Limiting** | HTTP 429 on $>10$ req/min | **Enforced** | Sliding-window in-memory rate limiter |
| **High-Volume Data Seeding** | Instant Priming | **0.15 seconds** | `scripts/seed_performance_data.py` |

---

### 3. Architecture & 3NF Database Foundation

```
┌────────────────────────────────────────────────────────────────────────┐
│                          VERISUB ARCHITECTURE                          │
├────────────────────────────────────────────────────────────────────────┤
│  Frontend (React + Vite + Tailwind + TanStack Query + Recharts)        │
│  ├── Apple Store Minimal Clean Light Design System                    │
│  ├── Paddle B2B SaaS High-Contrast Financial Cards                     │
│  └── Solana PublicNode Live Infrastructure RPC Telemetry Badges       │
├────────────────────────────────────────────────────────────────────────┤
│  API Gateway & Security (FastAPI + JWT + Sliding Window Limiter)       │
│  ├── Multi-Tenant Isolation via organization_id                       │
│  ├── Role-Based Access Control (ADMIN, STAFF, CUSTOMER)               │
│  └── Argon2id Password Hashing with OWASP Strict Policy                │
├────────────────────────────────────────────────────────────────────────┤
│  Core Domain Engines                                                   │
│  ├── Catalog & Quotation Engine (Frozen Price Snapshots)               │
│  ├── Subscription Lifecycle Engine & Digital Twin                      │
│  ├── Automated Billing Engine (Idempotent Runs + Taxes + Discounts)    │
│  ├── Contract-to-Bill Verification (SLA vs Telemetry + Credits)        │
│  └── Settlement Engine (Simulated Gateway + Payment Allocations)      │
├────────────────────────────────────────────────────────────────────────┤
│  Persistence & Cryptography                                            │
│  ├── 3NF Normalized Relational Schema (PostgreSQL / SQLite)            │
│  ├── Linear Alembic Migrations                                         │
│  └── SHA-256 Tamper-Evident Blockchain Audit Hash-Chain               │
└────────────────────────────────────────────────────────────────────────┘
```

---

### 4. Team Member Roles & Individual Deliverables

#### Member 1: Database Architect + Integration Lead
- **Responsibilities**: 3NF schema normalization, Alembic linear migrations, Argon2id authentication, RBAC authorization (`ADMIN`, `STAFF`, `CUSTOMER`), and tenant isolation.
- **Key Code Deliverables**:
  - `docs/DATABASE_SCHEMA.md`: 3NF Mermaid ER diagram.
  - `app/models/`: Normalized models (`auth.py`, `catalog.py`, `customer.py`, `quotation.py`, `subscription.py`, `billing.py`, `verification.py`).
  - `app/core/security.py`: Argon2id password hashing and OWASP password policy verification.
  - `alembic/versions/`: Linear zero-conflict migration chain.
- **Evaluation Defense Focus**:
  - Multi-tenant data segregation enforced at the database level.
  - Precision monetary arithmetic via `NUMERIC(12,2)` and Python `Decimal` (zero float round-off errors).
  - Cascade delete constraints protecting customer integrity.

#### Member 2: Core Subscription Backend Developer
- **Responsibilities**: Customer CRUD, product catalog with variant pricing, plan policy toggles, quotation pricing snapshots, and subscription state machine.
- **Key Code Deliverables**:
  - `app/modules/products/`: Additive variant pricing (`+ ₹560.00 Odoo Brand`).
  - `app/modules/plans/`: Plan policies (`is_pausable`, `is_renewable`, `is_closable_early`, `is_auto_close_at_end`).
  - `app/modules/quotations/`: Freezing price snapshots upon quotation confirmation.
  - `app/modules/subscriptions/`: State machine enforcing legal transitions (`ACTIVE` ↔ `PAUSED` → `CLOSED`) and Digital Twin generation.
- **Evaluation Defense Focus**:
  - How quotations prevent future catalog price increases from changing active customer rates.
  - State machine transition validation and audit event generation.

#### Member 3: Billing + Verification + Intelligence Lead
- **Responsibilities**: Idempotent recurring billing run, duplicate invoice prevention, tax calculation, discount decrementing, SLA contract verification, and SHA-256 hash-chain audit ledger.
- **Key Code Deliverables**:
  - `app/modules/billing/`: Automated billing runs with uniqueness constraint `(subscription_id, period_start, period_end)`.
  - `app/modules/billing/`: Rule-based GST tax engine and discount usage counters.
  - `app/modules/verification/`: Telemetry vs contract SLA evaluation generating automatic service credits.
  - `app/modules/verification/`: Cryptographic SHA-256 blockchain audit chain where modifying any database block invalidates the entire chain.
- **Evaluation Defense Focus**:
  - Prevention of double-billing via database-level unique constraints.
  - Telemetry verification formula calculating SLA service credit adjustments.
  - Cryptographic verification demonstrating tamper detection.

#### Member 4: Frontend + User Experience Developer
- **Responsibilities**: Design system fusion (Apple Store minimal light layout + Paddle SaaS billing cards + Solana PublicNode live node status badges), 1-click persona switcher, printable invoices, and sub-100ms dashboard interaction.
- **Key Code Deliverables**:
  - `frontend/src/components/layout/TopNav.tsx`: Live Solana PublicNode telemetry badge (`NODE LIVE | 32ms | 99.98% SLA`) and 1-click persona switcher.
  - `frontend/src/features/dashboard/Dashboard.tsx`: High-contrast financial MRR cards, velocity charts, and overdue invoices table.
  - `frontend/src/features/invoices/InvoiceList.tsx`: Itemized printable tax invoice view and simulated gateway payment receipt modal.
  - `frontend/src/features/verification/VerificationList.tsx`: SLA availability matrix and tamper-evident cryptographic verifier.
- **Evaluation Defense Focus**:
  - Sub-100ms UI responsiveness achieved via `selectinload` eager loading and normalized paginated array adapters.
  - Seamless persona simulation without logging in/out.

---

### 5. Step-by-Step Evaluator Demo & Video Script

#### Slide 1 / Screen 1: Top Navigation & Persona Switching (0:00 - 0:35)
* **Visual**: Open `http://localhost:3000`. Show the Top Navigation bar.
* **Action**:
  - Hover over the Solana PublicNode badge: `NODE LIVE | 32ms | 99.98% SLA`.
  - Click the **Role Switcher** dropdown (`ADMIN` ↔ `STAFF` ↔ `CUSTOMER`).
* **Script**:
  > *"Welcome to VERISUB, our Intelligent Subscription & Billing Verification Platform. Our interface is inspired by Apple's standard minimal layout combined with Paddle's fintech card design and Solana PublicNode's live infrastructure telemetry. The top navigation features live RPC node telemetry showing latency and uptime SLA. The 1-click persona switcher allows evaluators to simulate Admin, Staff, and Customer roles instantly."*

#### Slide 2 / Screen 2: Finance Executive Dashboard (0:35 - 1:10)
* **Visual**: Dashboard view showing MRR, Revenue, Outstanding, and Overdue.
* **Action**:
  - Scroll past the stat cards and hover over the Revenue Velocity bar chart.
  - Show the Invoices Requiring Attention table.
* **Script**:
  > *"Our executive dashboard computes metrics across 5,000 invoices and 1,000 subscriptions in under 95 milliseconds using single-pass SQL aggregations. Notice our MRR of $128,450, total revenue collected of $1.65M, and immediate surfacing of overdue invoices requiring team follow-up."*

#### Slide 3 / Screen 3: Product Catalog, Variants & Plan Policies (1:10 - 1:45)
* **Visual**: Navigate to **Products & Plans**.
* **Action**:
  - Show the Products table with the `+ $560.00 Odoo Brand` variant badge.
  - Click the **Plans** tab and highlight the 4 flag badges: `[Pausable]`, `[Renewable]`, `[Early Close]`, and `[Auto-Close]`.
* **Script**:
  > *"In our catalog, products support additive pricing deltas—such as our Odoo Brand variant adding 560 to the base price. Plans feature 4 discrete database flags governing customer lifecycle operations: pausable, renewable, early closure, and auto-close at contract termination."*

#### Slide 4 / Screen 4: Quotation Conversion & Digital Twin (1:45 - 2:20)
* **Visual**: Navigate to **Subscriptions**, then click a subscription row.
* **Action**:
  - Show the **Subscription Digital Twin** view.
  - Click **Pause Subscription**, type a reason, and confirm -> status turns `PAUSED`.
  - Click **Resume Subscription** -> status returns to `ACTIVE`.
* **Script**:
  > *"Quotations freeze line item pricing snapshots so future catalog edits never modify active contracts. In the Subscription Digital Twin, team members see contract terms, live billing state, and event history. Our state machine validates operations: pausing requires an audit explanation and immediately updates the digital twin."*

#### Slide 5 / Screen 5: Automated Billing & Simulated Payment Gateway (2:20 - 2:55)
* **Visual**: Navigate to **Invoices**.
* **Action**:
  - Click any invoice to open the itemized printable invoice layout.
  - Click **Pay with Gateway** -> select Card or UPI -> click **Authorize Payment** -> invoice status updates to `PAID`.
* **Script**:
  > *"Our recurring billing run auto-generates invoices from active subscriptions. A unique database constraint on subscription ID, period start, and period end strictly prevents duplicate billing. Invoices format into printable tax documents with GST breakdown, and team members can process payments through our simulated payment gateway."*

#### Slide 6 / Screen 6: SLA Verification & SHA-256 Audit Blockchain (2:55 - 3:30)
* **Visual**: Navigate to **Verification & Audit**.
* **Action**:
  - Show the SLA telemetry table and automatic service credit calculation.
  - Scroll down to the **Cryptographic Audit Trail** and point out `current_hash` and `previous_hash`.
* **Script**:
  > *"Our core innovation is Contract-to-Bill Value Verification. Live service telemetry is evaluated against contractual uptime SLAs. If an outage breaches the SLA, our engine automatically computes compensatory service credits. Every billing event and state transition is cryptographically sealed in a SHA-256 blockchain audit ledger, where any unauthorized database tampering is immediately detected. Thank you."*
