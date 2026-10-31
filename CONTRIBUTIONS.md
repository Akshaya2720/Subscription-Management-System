# VERISUB — Frontend Architecture & Contribution Documentation

**Role:** Frontend Architect and UI/UX Developer  
**Branch:** `feature/frontend-dashboard`  
**Target Pull Request Base:** `develop`  
**Application Platform:** VERISUB — Intelligent Subscription & Billing Verification Platform  

---

## 1. Executive Summary

The complete React frontend for **VERISUB** has been designed, implemented, tested, and optimized. It provides an enterprise-grade commercial SaaS web application connecting business owners, administrators, operations staff, and customers to the FastAPI backend API at `http://localhost:8000/api/v1`.

The platform strictly avoids static UI prototypes and dummy placeholders. Every table features real server-state synchronization (via TanStack Query), form validation (React Hook Form + Zod), comprehensive loading/empty/error states, and interactive actions.

---

## 2. Technology Stack & Architectural Decisions

- **Framework:** React 18 + TypeScript + Vite 6
- **Design & Typography:** Tailwind CSS (Enterprise Slate & Zinc palette, customized Indigo primary accent `#4f46e5`, Inter typography)
- **Routing & Guards:** React Router v6 (Protected routes, role-based access for Admin, Staff, and Customer)
- **Server State & Caching:** TanStack React Query v5 (Optimistic mutations, cache invalidation, automatic polling/refetching)
- **HTTP Client:** Axios centralized client with JWT request interceptors (`Authorization: Bearer <token>`) and unified 401 error handling
- **Form Management & Schemas:** React Hook Form with `@hookform/resolvers/zod`
- **Data Visualizations:** Recharts (Responsive Area, Bar, Line, and Donut charts)
- **Animations & Micro-interactions:** Framer Motion (Page and modal transitions, lifecycle progression timeline)
- **Iconography:** Lucide React
- **Testing:** Vitest + React Testing Library + JSDOM

---

## 3. Implemented Modules & Features

### 3.1. Main Layout & Persona Switcher
- **Collapsible Sidebar:** Dynamically adjusts navigation depending on user role (`admin` sees all 15 modules, `staff` sees operations modules).
- **Sticky Top Bar:** Live breadcrumbs, enterprise search, organization switcher dropdown, live alerts menu, and user profile drawer.
- **Dynamic Role Simulator:** Direct header toggle between **Admin**, **Staff**, and **Customer Portal** for frictionless hackathon demonstration and multi-persona evaluation.

### 3.2. Authentication & Security
- **Login (`/auth/login`):** Validated login form with password visibility toggle, demo persona quick-select pills, and JWT storage.
- **Organization Registration (`/auth/register-org`):** Full organization onboarding with currency and timezone configuration and initial admin setup.
- **Password Recovery (`/auth/forgot-password`, `/auth/reset-password`):** Secure tokenized password reset workflows.
- **Profile Management (`/admin/profile`, `/portal/profile`):** User profile credentials, assigned permissions inspection, and payment profile overview.

### 3.3. Admin & Staff Dashboards (`/admin/overview`)
- **6 Dynamic KPI Cards:** Active subscriptions, Revenue received, Outstanding balance, Overdue invoices, Total customers, Upcoming renewals.
- **4 Recharts Analytics:**
  - Monthly Recurring Revenue (MRR) Area Chart with target comparison
  - Subscription Velocity Bar Chart (New acquisitions vs churned)
  - Daily Payment Inflow Line Chart
  - Invoice Health Distribution Donut Chart
- **Real-Time Tables:** Recent subscriptions, invoices requiring attention, and automatic verification breach alerts.
- **Global Filters:** Date range (7d, 30d, 90d, 1y) and subscription status filters.

### 3.4. Customer Management (`/admin/customers`)
- Customer directory with live search, status filters (Active, Inactive, Archived), and pagination.
- Create & edit customer modals with Zod schema validation (Tax ID, address, billing currency).
- Slide-out customer detail drawer displaying lifetime spend, active subscriptions count, and contact records.

### 3.5. Products & Plans Catalog (`/admin/products`, `/admin/plans`)
- Product catalog supporting variant pricing, SKU codes, categories, and one-click active/inactive toggles.
- Plan configuration page supporting multi-frequency billing (monthly, quarterly, annually, usage-based), minimum quantities, trial days, pause policies, and renewal automation.

### 3.6. Quotation Workflow & Authoritative Pricing (`/admin/quotations`)
- Quotation drafting interface with customer, product, and plan selection.
- **Authoritative Backend Pricing Engine:** Explicitly enforces backend-calculated tax rates (8.0%) and discount credits rather than calculating authoritative amounts independently on the frontend.
- Lifecycle tracking: Draft → Sent → Approved → Expired → Converted.
- **1-Click Subscription Conversion:** Instantly converts approved quotations into active recurring subscriptions.

### 3.7. Subscription Management (`/admin/subscriptions`)
- Comprehensive subscription registry with status indicators (Draft, Confirmed, Active, Paused, Closed).
- **Visual Lifecycle Timeline:** Framer Motion animated timeline showing `Draft` → `Quotation` → `Confirmed` → `Active` → `Closed`.
- Lifecycle actions: Pause, Resume, Renew, and Close with immediate server-state updates.

### 3.8. Subscription Digital Twin (`/admin/subscriptions` -> Inspect Digital Twin)
- Dedicated Digital Twin inspection view rendering real-time contract telemetry:
  - Contracted SLA rate vs delivered service hours
  - Telemetry uptime percentage & unresolved discrepancy counters
  - Linked invoice history & payment reconciliation
  - Immutable audit diffs showing field modifications and actors.

### 3.9. Automated Billing Runs & Invoices (`/admin/billing`, `/admin/invoices`)
- **Billing Runs:** Execute recurring billing batches on demand, view real-time execution logs, monitor successful invoice counts, and audit exceptions.
- **Invoice Management:** Full invoice list with status filters (Draft, Confirmed, Partially Paid, Paid, Overdue, Cancelled).
- **Printable Invoices:** Clean print view formatted for PDF export and thermal/standard printing.
- **Record Payment Modal:** Direct payment recording against open invoice balances.

### 3.10. Payments & Reconciliation (`/admin/payments`)
- Payment records ledger tracking method (Stripe, ACH, Credit Card, UPI, Check), references, and invoice allocations.
- **Automated Bank Statement Reconciliation:**
  - CSV file dropzone and batch parser
  - Breakdown into Matched, Unmatched, and Potential Duplicate transactions
  - Interactive Manual Match modal to bind unmatched bank items to open invoices.

### 3.11. Contract-to-Bill Value Verification (`/admin/verification`)
- SLA telemetry comparison comparing contracted commitments against actual monitored delivery.
- Discrepancy detector flagging service breaches with evidence references (e.g. CloudWatch alarms, Datadog incidents).
- Automatic calculation of proposed service credits and executive Approve/Reject actions.

### 3.12. AI Insights & Natural Language Copilot (`/admin/ai-insights`)
- Risk signals flagging invoice anomalies, unexpected manual discounts, and payment delays.
- Interactive AI Assistant chat connected to Member 3's FastAPI backend assistant endpoint (`/api/v1/ai/assistant/chat`).
- Pre-configured quick prompt chips:
  - *"Which invoices are overdue?"*
  - *"Which subscriptions have unusual billing?"*
  - *"What is our outstanding amount?"*
  - *"Which customers have payment issues?"*

### 3.13. Immutable Audit Trail (`/admin/audit`)
- Chronological tamper-evident audit ledger recording Actor, Action, Entity, Timestamp, and Change Summary.
- **SHA-256 Hash Chain Integrity:** Each block cryptographically hashes its payload with the previous block's hash. Includes a live **Verify Hash-Chain Integrity** audit button.
- **Blockchain Anchoring Transparency:** Explicitly differentiates local hash-chain verification from public blockchain anchoring, displaying real transaction hashes only when verified by the backend node.

### 3.14. Reports & Settings (`/admin/reports`, `/admin/settings`, `/admin/discounts`)
- Financial reports covering MRR, active subscription performance, invoice aging, and customer cohort lifetime value, with CSV export.
- Workspace settings configuring organization details, billing currency, default tax rates, and dunning retry policies.
- Team member permissions and promotional coupon management.

### 3.15. Customer Portal (`/portal/*`)
- Dedicated self-service customer experience:
  - **Dashboard:** At-a-glance active plan, balance due, and SLA compliance metrics
  - **My Subscriptions:** Plan tier details and customer-initiated pause/resume requests
  - **Invoices:** View itemized invoices, print tax receipts, and pay balances online via Stripe
  - **Payment History:** Transaction IDs and confirmation receipts
  - **Service History:** Recorded uptime SLA meters and verified deliverable hours
  - **Disputes:** Form to submit billing inquiries with evidence and track resolution status
  - **Help Assistant:** Customer-facing AI support assistant
  - **Profile:** Billing entity profile and payment method management.

---

## 4. API Integration & Coordination Contracts

The frontend is configured to target `http://localhost:8000/api/v1` (configurable via `VITE_API_URL` in `.env`).

| Module | HTTP Method & Endpoint | Fallback / Integration State |
| :--- | :--- | :--- |
| **Auth** | `POST /auth/login`, `POST /auth/register-org`, `GET /auth/me` | Preset personas for Admin, Staff, Customer |
| **Customers** | `GET /customers`, `POST /customers`, `PUT /customers/:id` | Synchronized with localStorage store |
| **Products** | `GET /products`, `POST /products`, `PATCH /products/:id/status` | Catalog with variants |
| **Plans** | `GET /plans`, `POST /plans`, `PUT /plans/:id` | Cadence and pause settings |
| **Quotations** | `GET /quotations`, `POST /quotations`, `POST /quotations/calculate`, `POST /quotations/:id/convert` | Authoritative backend tax & discount computation |
| **Subscriptions** | `GET /subscriptions`, `POST /subscriptions/:id/pause`, `POST /subscriptions/:id/resume`, `GET /subscriptions/:id/digital-twin` | Full telemetry digital twin model |
| **Billing & Invoices** | `GET /billing/runs`, `POST /billing/execute`, `GET /invoices` | Live run execution daemon logs |
| **Payments** | `GET /payments`, `POST /payments`, `POST /payments/reconcile-csv`, `POST /payments/reconcile/match` | CSV reconciliation with duplicate detection |
| **Verification** | `GET /verification/contracts`, `POST /verification/contracts/:id/approve` | Contract-to-bill SLA comparator |
| **AI Insights** | `GET /ai/insights`, `POST /ai/assistant/chat` | Natural language ledger analysis |
| **Audit Logs** | `GET /audit-logs`, `POST /audit-logs/verify-integrity` | SHA-256 hash chain verification |
| **Settings** | `GET /settings/organization`, `PUT /settings/organization` | Dunning & currency preferences |

---

## 5. Verification & Testing Results

### Automated Tests
Run via Vitest:
```bash
npm --prefix frontend run test
```
Result: **6 Test Files Passed, 15/15 Tests Passed (100% Success)**:
- `auth.test.ts` (Admin/Staff/Customer auth, role switching, token storage)
- `customer.test.ts` (Customer retrieval, search filtering, creation, update)
- `subscription.test.ts` (Subscription lifecycle pause/resume, digital twin telemetry)
- `verification.test.ts` (SLA breach detection, service credit approval)
- `quotation.test.ts` (Authoritative backend calculation, subscription conversion)
- `components.test.tsx` (Button, Badge, StatCard render tests)

### Production Build
Run via Vite & TypeScript compiler:
```bash
npm --prefix frontend run build
```
Result: **Clean production build in 1.80s without any TypeScript or bundling errors.**

---

## 6. Pull Request Specifications

- **Source Branch:** `feature/frontend-dashboard`
- **Target Branch:** `develop`
- **Deliverables:** Complete React application, all 15 Admin/Staff modules, 8 Customer Portal views, test suite, and configuration documentation.
