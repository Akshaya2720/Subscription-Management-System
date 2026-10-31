# VERISUB Contributions & Engineering Log

---

# PART 1: Database Architecture, Authentication & Integration Lead

**Role:** Database Architect, Authentication and Integration Lead  
**Branch:** `feature/database-auth`  
**Repository:** `https://github.com/Akshaya2720/Subscription-Management-System`

---

## 1. Overview of Implemented Modules

As the Database Architect, Authentication, and Integration Lead for VERISUB, I have designed and implemented the complete shared backend foundation, authentication engine, role-based access control (RBAC), multi-tenant organization isolation, and customer management system.

All deliverables are production-grade implementations adhering to SQLAlchemy 2.0, Pydantic v2, FastAPI, and Alembic standards.

---

## 2. Core Architecture & Implemented Components

### 2.1 Database Architecture (SQLAlchemy 2.0 & PostgreSQL/SQLite)
- **Base & Mixins:**
  - `Base`: Declarative base with SQLAlchemy 2.0 typed mapped columns.
  - `TimestampMixin`: Timezone-aware `created_at` and `updated_at` timestamps using `func.now()`.
- **Foundational Models (13 Normalized Relational Tables):**
  - `Organization`: Primary tenant model with status indexing and UUID primary keys.
  - `OrganizationSettings`: 1:1 tenant settings covering default currency, timezone, tax configuration (JSON), and billing preferences (JSON).
  - `User`: Central user identity with unique email index, Argon2id password hash, and active/verification flags.
  - `Membership`: Multi-tenant organization membership model enabling users to join multiple organizations with unique `(organization_id, user_id)` constraint.
  - `Role`: System roles (`ADMIN`, `STAFF`, `CUSTOMER`).
  - `Permission`: 12 granular platform permissions (e.g. `MANAGE_ORGANIZATION`, `MANAGE_STAFF`, `MANAGE_CUSTOMERS`, etc.).
  - `RolePermission`: Association table linking roles to permissions.
  - `MembershipRole`: Association table linking organization memberships to assigned roles.
  - `Customer`: B2B customer business profile decoupled from user logins, scoped by `organization_id` with unique `customer_code` per organization.
  - `CustomerAddress`: Structured customer addresses (billing, shipping).
  - `CustomerContact`: Customer points of contact with primary contact management.
  - `RefreshToken`: Cryptographically hashed refresh tokens with expiration and explicit revocation tracking (`revoked_at`).
  - `PasswordResetToken`: Secure single-use hashed reset tokens with expiration and consumption timestamp (`used_at`).

### 2.2 Security & Authentication Engine
- **Argon2id Hashing:** Password hashing using `argon2.PasswordHasher(type=argon2.Type.ID)`.
- **Password Complexity Validation:** Enforces minimum 9 characters, uppercase, lowercase, digit, and special characters.
- **JWT Generation & Claims:** Scoped access tokens (`HS256`, 30 min default) and refresh tokens (7 days default) with user ID (`sub`) and tenant organization context.
- **Refresh Token Rotation:** Refresh endpoint rotates the token pair and revokes the consumed token, preventing replay attacks.
- **Logout & Revocation:** Secure session invalidation in database.
- **Password Reset Flow:** Secure token generation and hashing. Transparent dev-mode fallback when SMTP is unconfigured.
- **Password Change:** Secure credential update with mandatory current password re-verification and session revocation.

### 2.3 Role-Based Access Control (RBAC) & Tenant Isolation
- **Dependency Factories:**
  - `get_current_user`: Extracts and decodes JWT, verifies user active status.
  - `get_current_membership`: Validates tenant context from `X-Organization-ID` header and verifies active membership in database.
  - `require_role(*roles)`: Enforces role requirements.
  - `require_permissions(*permissions)`: Checks effective permissions resolved across all assigned membership roles.
- **Multi-Tenant Protection:** Every customer, user, and organization query enforces `organization_id` matching to eliminate cross-tenant data leaks.

### 2.4 API Routers & Central Application (`/api/v1/`)
- **Authentication (`/api/v1/auth`):**
  - `POST /register`: Atomic registration of organization, settings, admin user, membership, and default roles.
  - `POST /login`: Multi-tenant login with organization disambiguation.
  - `POST /refresh`: Refresh token rotation.
  - `POST /logout`: Refresh token revocation.
  - `POST /forgot-password`: Password reset dispatch.
  - `POST /reset-password`: Reset confirmation and token consumption.
  - `GET /me`: Authenticated user profile with memberships.
  - `PATCH /me`: Profile update.
  - `POST /change-password`: Password change.
- **Organizations (`/api/v1/organizations`):**
  - `POST /`: Create a new organization context as an authenticated user (`create_organization`).
  - `GET /current`: Current organization profile.
  - `PATCH /current`: Update organization attributes (`MANAGE_ORGANIZATION`).
  - `GET /current/settings`: Get tenant settings (`MANAGE_SETTINGS`).
  - `PATCH /current/settings`: Update tenant settings (`MANAGE_SETTINGS`).
- **Users (`/api/v1/users`):**
  - `GET /`: Paginated organization staff listing (`MANAGE_STAFF`).
  - `POST /staff`: Create staff account in current organization (`MANAGE_STAFF`, ADMIN only).
  - `GET /{user_id}`: User lookup with tenant verification.
  - `PATCH /{user_id}`: Update user state.
  - `DELETE /{user_id}`: Deactivate user organization membership.
- **Customers (`/api/v1/customers`):**
  - `POST /`: Create customer record with tenant isolation (`MANAGE_CUSTOMERS`).
  - `GET /`: Paginated customer search and filtering (`MANAGE_CUSTOMERS`).
  - `GET /{customer_id}`: Customer lookup with tenant isolation.
  - `PATCH /{customer_id}`: Update customer record.
  - `DELETE /{customer_id}`: Soft-delete/deactivate customer.
  - `POST /{customer_id}/addresses`: Add customer address.
  - `POST /{customer_id}/contacts`: Add customer contact.

### 2.5 Database Migrations (Alembic)
- Fully configured `alembic.ini` and `backend/alembic/env.py`.
- Migration `0347c260dea1_initial_schema.py` auto-generates and manages all 13 tables, foreign keys, unique constraints, and indexes.
- Verified both upgrade (`upgrade head`) and downgrade (`downgrade base`).

---

## 3. Files Created and Modified

```
backend/
├── .env.example
├── alembic.ini
├── requirements.txt
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       ├── __init__.py
│       └── 0347c260dea1_initial_schema.py
├── app/
│   ├── main.py
│   ├── core/
│   │   ├── config.py
│   │   ├── permissions.py
│   │   └── security.py
│   ├── db/
│   │   ├── base.py
│   │   └── session.py
│   ├── dependencies/
│   │   ├── __init__.py
│   │   └── auth.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── customer.py
│   │   ├── membership.py
│   │   ├── organization.py
│   │   ├── role.py
│   │   ├── token.py
│   │   └── user.py
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── customers.py
│   │   ├── organization.py
│   │   └── users.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── common.py
│   │   ├── customer.py
│   │   ├── organization.py
│   │   └── user.py
│   └── services/
│       ├── __init__.py
│       ├── auth_service.py
│       ├── customer_service.py
│       ├── organization_service.py
│       └── user_service.py
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_auth.py
    ├── test_customer.py
    └── test_rbac.py
.gitignore
CONTRIBUTIONS.md
```

---

## 4. Test Suite & Verification Results

Executed full pytest suite against all functional domains:

```
====================== 57 passed, 116 warnings in 17.73s ======================
```

### Breakdown of Verified Scenarios:
1. **Authentication Tests (`test_auth.py` - 26 tests):**
   - Organization registration with default ADMIN role.
   - Duplicate organization email & duplicate admin email rejection (409 Conflict).
   - Password complexity enforcement (length, uppercase, lowercase, digit, special character).
   - Login credential verification, invalid credentials rejection (401 Unauthorized).
   - Token refresh rotation and invalid refresh token rejection.
   - Logout token revocation and subsequent refresh rejection.
   - Forgot-password flow with safe development-mode token output when SMTP is unconfigured.
   - Reset-password flow with token consumption and session invalidation.
   - Authenticated current user profile retrieval (`/auth/me`) and profile update.
   - Password change with old password verification and complexity validation.
2. **RBAC & Isolation Tests (`test_rbac.py` - 17 tests):**
   - Organization creation by authenticated user (`POST /organizations`) and duplicate email rejection.
   - Admin privileges (create staff, update org, manage customers).
   - Staff restrictions (cannot create staff, cannot modify organization settings, can manage operational customers).
   - Cross-organization customer isolation (Organization A cannot access Organization B's customer).
   - Cross-organization customer listing isolation.
   - Forged `X-Organization-ID` header protection (returns 403 Forbidden).
   - Staff pagination, detail lookup, and deactivation.
   - Duplicate staff email rejection within the organization.
3. **Customer Operations Tests (`test_customer.py` - 14 tests):**
   - Customer creation with unique `customer_code` per organization.
   - Duplicate customer code rejection within the same organization.
   - Paginated customer listings, search by company name, and status filtering.
   - Customer detail lookup and 404 handling.
   - Customer update and soft-deletion (status transitioned to `inactive`).

---

# PART 2: Subscription Engine Backend Developer Contribution

**Role**: Subscription Engine Backend Developer  
**Assigned Branch**: `feature/subscription-engine`  
**Target Branch for PR**: `develop`

---

## 1. Summary of Delivered Work

As the Subscription Engine Backend Developer for VERISUB, I have designed, implemented, migrated, and thoroughly verified the entire subscription business lifecycle. All financial operations utilize high-precision Python `Decimal` / SQL `Numeric(14, 2)` (no floating point calculations), all primary keys use standard UUIDs, and every domain query is strictly protected by multi-tenant `organization_id` isolation.

---

## 2. Modules & Capabilities Delivered

### A. Core Architecture & Member 1 Foundation Integration
- **`app/core/database.py`**: SQLAlchemy 2.0 DeclarativeBase engine, session maker, SQLite PRAGMA foreign keys, and `get_db` dependency.
- **`app/core/auth.py`**: Integration with Member 1's models (`Organization`, `User`) and dependencies (`get_current_organization`, `get_current_user`). Ensures strict multi-tenant data boundaries.
- **`app/core/config.py`**: Environment and runtime configuration using Pydantic v2 `SettingsConfigDict`.
- **`app/core/exceptions.py`**: Domain exceptions for HTTP error translation (`EntityNotFoundException`, `DuplicateEntityException`, `InvalidStateTransitionException`, `BusinessRuleValidationException`).

### B. Customer Management (`app/modules/customers`)
- **Models & Unique Constraints**: `uq_org_customer_code` and `uq_org_customer_email`.
- **CRUD Operations**: Create, update, soft-delete/deactivate customer (`status="INACTIVE"`).
- **Search & Pagination**: Query matching customer code, company, contact name, or email with configurable `page` and `per_page`.
- **History Integrations**: Endpoints to view customer subscription history and real billing invoice history (`GET /customers/{id}/invoices`, `GET /customers/{id}/subscriptions`).

### C. Product & Variant Management (`app/modules/products`)
- **Product Model**: `id`, `organization_id`, `name`, `product_type`, `description`, `sales_price` (Decimal), `cost_price` (Decimal), `notes`, `status`.
- **Variant Model**: `id`, `product_id`, `variant_name`, `description`, `additional_price` (Decimal), `status`.
- **CRUD & Deactivation**: Product CRUD, variant CRUD under product or directly, search, filtering, and safe deactivation/archival.

### D. Subscription Plan Management (`app/modules/plans`)
- **Plan Model**: `id`, `organization_id`, `name`, `description`, `billing_frequency` (DAILY, WEEKLY, MONTHLY, YEARLY), `plan_price` (Decimal), `minimum_quantity`, `start_availability_date`, `end_availability_date`, and policy JSON fields (`auto_close_configuration`, `early_closure_configuration`, `pause_configuration`, `renewal_configuration`).
- **Plan Price History**: Implemented `PlanPriceHistory` table. Updates to plan prices automatically record new audit entries without silently mutating contracted subscription prices.
- **Validations**: Availability dates validation and frequency validation.

### E. Quotation Management (`app/modules/quotations`)
- **Models**: `Quotation` and `QuotationItem` with immutable pricing snapshots.
- **Totals Calculation**: Integrated with Member 3's `DefaultTaxDiscountService` interface computing subtotal, discount, tax breakdown, and grand total.
- **Workflow & Expiry**: `DRAFT` -> `CONFIRMED` -> `CONVERTED` or `CANCELLED`. Validates expiry date against current date before confirmation.
- **Conversion to Subscription**: Converts confirmed quotation directly to an active/confirmed subscription with locked pricing snapshots.

### F. Subscription Lifecycle Management (`app/modules/subscriptions`)
- **State Machine (`lifecycle.py`)**: Validates state transitions (`DRAFT` / `CONFIRMED` -> `ACTIVE` -> `PAUSED` -> `ACTIVE` -> `CLOSED`). Blocks invalid or illegal transitions (e.g. activating expired subscriptions, resuming unpaused subscriptions).
- **Interval Calculations**: Deterministic calculation of `next_billing_date` and renewal extension for `DAILY`, `WEEKLY`, `MONTHLY`, and `YEARLY` cycles.
- **Audit Logging**: `SubscriptionEvent` records every lifecycle transition, change, pause reason, renewal, or early termination fee.

### G. Subscription Digital Twin (`app/modules/subscriptions/digital_twin.py`)
- Live endpoint `GET /subscriptions/{id}/digital-twin` that aggregates **real database records** (no mock data):
  - Customer profile and tax identifier
  - Subscription items with contractual snapshot prices
  - Plan availability and catalog price
  - Linked quotations
  - Billing invoices and payments from Member 3's billing data
  - Chronological subscription change history
  - Financial verification status

### H. Change Impact Analysis (`app/modules/subscriptions/impact_analysis.py`)
- Endpoints:
  - `POST /api/v1/change-impact/product`
  - `POST /api/v1/change-impact/plan`
- Previews the financial and operational impact of proposed catalog changes before applying them:
  - Reports affected active subscriptions
  - Calculates protected recurring revenue
  - Lists pending quotations referencing the item
  - Enforces policy guarantee: *"Existing customer subscriptions retain their agreed contractual snapshot price."*

### I. Database Migrations (Alembic)
- Migration generated and applied: `127056ed81a1_initial_subscription_engine_tables.py` creating all 11 tables and multi-tenant unique indexes.

---

## 3. Team Coordination & Interfaces

### Member 1 (Database, Auth, Multi-Tenancy)
- Reused SQLAlchemy Base, database session, and models for `Organization` and `User`.
- Enforced `organization_id` foreign key and query filtering across all 11 tables.

### Member 3 (Billing & Verification)
- Defined `TaxDiscountServiceInterface` in `app/modules/billing/interfaces.py` and implemented `DefaultTaxDiscountService`.
- Agreed on billing frequency, `next_billing_date`, and input payloads for invoice generation.
- Created `Invoice` and `Payment` tables to seamlessly integrate real billing history into customer and Digital Twin endpoints without competing invoice engines.

### Member 4 (Frontend Dashboard)
- Standardized RESTful routes under `/api/v1/`.
- Clear, type-safe Pydantic v2 schemas with rich descriptions, pagination models, and enum values.
- Self-documenting OpenAPI Swagger UI available at `/docs`.

---

## 4. Verification and Test Results

A full suite of 19 automated integration and unit tests was written using `pytest` and `fastapi.testclient.TestClient`:

```bash
.venv/bin/pytest -v
```

### Test Coverage Summary:
- `tests/test_customers.py`:
  - `test_customer_crud`: PASSED
  - `test_duplicate_customer_handling`: PASSED
  - `test_customer_search_filter_pagination`: PASSED
- `tests/test_products_variants.py`:
  - `test_product_crud_and_variants`: PASSED (verifies ₹560 variant pricing and Decimal math)
  - `test_duplicate_product_name`: PASSED
  - `test_product_search_and_filter`: PASSED
- `tests/test_plans.py`:
  - `test_plan_crud_and_price_history`: PASSED (verifies price revision history logging)
  - `test_plan_frequency_validation`: PASSED
  - `test_plan_availability_date_validation`: PASSED
- `tests/test_quotations.py`:
  - `test_quotation_lifecycle_and_conversion`: PASSED (verifies price snapshots, GST calculations, and subscription conversion)
  - `test_quotation_expiry_validation`: PASSED
  - `test_quotation_cancellation`: PASSED
- `tests/test_subscriptions.py`:
  - `test_subscription_complete_lifecycle`: PASSED (Draft -> Active -> Pause -> Resume -> Renew -> Close)
  - `test_invalid_state_transitions`: PASSED
  - `test_subscription_search_filter_pagination`: PASSED
- `tests/test_digital_twin.py`:
  - `test_digital_twin_accuracy`: PASSED (aggregates real customer, item, invoice, payment, and audit records)
- `tests/test_impact_analysis.py`:
  - `test_product_change_impact_analysis`: PASSED (verifies contract price protection)
  - `test_plan_change_impact_analysis`: PASSED
- `tests/test_organization_isolation.py`:
  - `test_cross_organization_isolation`: PASSED (guarantees complete isolation between organizations)

**Result**: 19 passed in ~1.0s.

---

# PART 3: Frontend Architecture & Contribution Documentation

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
