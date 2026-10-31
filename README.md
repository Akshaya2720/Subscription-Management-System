# VERISUB — Intelligent Subscription & Billing Verification Platform

VERISUB is an enterprise-grade subscription management, recurring billing, and service contract verification platform. Built with strict monetary precision, multi-tenant isolation, cryptographic audit trails, and automated SLA reconciliation, VERISUB guarantees that businesses only bill what was contracted, delivered, and mathematically verified.

---

## Table of Contents

1. [Platform Vision & Core Capabilities](#platform-vision--core-capabilities)
2. [Team Engineering Roles & Architectural Ownership](#team-engineering-roles--architectural-ownership)
3. [User Personas & Role-Based Access Control (RBAC)](#user-personas--role-based-access-control-rbac)
4. [Technology Stack](#technology-stack)
5. [Repository Structure](#repository-structure)
6. [Getting Started & Local Setup](#getting-started--local-setup)
   - [Backend Setup (FastAPI & SQLAlchemy)](#backend-setup)
   - [Database Migrations (Alembic)](#database-migrations)
   - [Frontend Setup (React + Vite + Tailwind)](#frontend-setup)
7. [API Endpoints Reference](#api-endpoints-reference)
8. [Automated Testing & Verification](#automated-testing--verification)

---

## Platform Vision & Core Capabilities

Modern subscription businesses suffer from billing leakage, SLA disputes, manual invoice errors, and disconnected product catalogs. VERISUB solves this with:

- **Immutable Price Snapshots**: Quotes and subscriptions lock unit rates at contract execution. Catalog updates never retroactively alter customer agreements.
- **Contract-to-Bill Value Verification**: Automatically correlates live telemetry uptime and delivered service hours against contractual commitments, flagging SLA breaches and auto-calculating service credits.
- **Subscription Digital Twin**: Real-time aggregation of customer profile, locked contract terms, live telemetry, invoice history, payment reconciliation, and audit events.
- **Change Impact Analysis**: Previews the financial and operational fallout of planned catalog price changes across all active subscriptions before applying them.
- **Automated Bank Reconciliation**: CSV statement ingestion with automatic and manual invoice payment matching.
- **AI-Powered Anomaly Detection & Copilot**: Detects billing irregularities, payment delays, and unusual manual discounts via an interactive assistant.
- **Cryptographic Audit Trail**: Tamper-evident SHA-256 hash chains verifying system integrity with blockchain anchoring readiness.

---

## Team Engineering Roles & Architectural Ownership

VERISUB was engineered collaboratively by four specialized roles:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                VERISUB PLATFORM ARCHITECTURE                           │
└────────────────────────────────────────────────────────────────────────────────────────┘
                                           │
         ┌─────────────────────────────────┼─────────────────────────────────┐
         ▼                                 ▼                                 ▼
┌──────────────────┐             ┌──────────────────┐             ┌──────────────────┐
│     ROLE 1       │             │     ROLE 2       │             │     ROLE 3       │
│  Database, Auth  │             │   Subscription   │             │     Billing,     │
│ & Integration    │             │      Engine      │             │ Verification, AI │
│     (Lead)       │             │     Backend      │             │  & Audit Engine  │
└──────────────────┘             └──────────────────┘             └──────────────────┘
         │                                 │                                 │
         └─────────────────────────────────┼─────────────────────────────────┘
                                           ▼
                         ┌──────────────────────────────────┐
                         │              ROLE 4              │
                         │    Frontend Architect & UI/UX    │
                         │   (React 18 + Vite + Tailwind)   │
                         └──────────────────────────────────┘
```

### Role 1: Database Architect, Authentication & Integration Lead
*Responsible for the core relational foundation, multi-tenant isolation, user identity, and RBAC.*
- **13 Foundational Relational Models**: Designed normalized schemas using SQLAlchemy 2.0 with UUID primary keys and timezone-aware timestamps (`organizations`, `organization_settings`, `users`, `memberships`, `roles`, `permissions`, `role_permissions`, `membership_roles`, `customers`, `customer_addresses`, `customer_contacts`, `refresh_tokens`, `password_reset_tokens`).
- **Argon2id Password Security**: Hardware-hardened password hashing via `argon2-cffi`. Enforces strict complexity (>8 characters, uppercase, lowercase, digit, and special characters).
- **JWT Authentication Engine**: Scoped access tokens (`HS256`, 30 min) and rotating refresh tokens (7 days) with database-backed token hashing, replay prevention, and logout revocation.
- **Multi-Tenant Protection**: Dynamic FastAPI dependencies (`get_current_membership`, `require_role`, `require_permissions`) enforcing tenant scoping via `X-Organization-ID` header. Prevents cross-organization data leakage.
- **Password Reset Flow**: Single-use hashed reset tokens with transparent development-mode fallback when SMTP is unconfigured.
- **Central API Routing & Integration**: Auth, Organization, User/Staff, and Customer endpoints under `/api/v1/`.

### Role 2: Subscription Engine Backend Developer
*Responsible for product catalogs, quotation workflows, subscription state machine, and digital twins.*
- **Product & Variant Catalog**: Products and SKU variants with high-precision Python `Decimal` / SQL `Numeric(14, 2)` monetary values.
- **Subscription Plans & Policy History**: Cadences (`DAILY`, `WEEKLY`, `MONTHLY`, `YEARLY`), trial periods, pause policies, and `PlanPriceHistory` audit logging.
- **Quotation Workflow & Authoritative Calculations**: Draft → Confirmed → Converted/Cancelled quote lifecycle with automatic tax/discount breakdown and instant conversion to active subscriptions.
- **Subscription Lifecycle State Machine**: Deterministic transitions (`DRAFT` → `CONFIRMED` → `ACTIVE` → `PAUSED` → `ACTIVE` → `CLOSED`), next billing interval calculations, and event logging.
- **Subscription Digital Twin (`/subscriptions/{id}/digital-twin`)**: Aggregates real contractual terms, SLA rates, invoices, and audit diffs into a unified telemetry model.
- **Change Impact Analysis (`/change-impact/*`)**: Real-time simulation of catalog price revisions against active recurring contracts.

### Role 3: Billing, Verification & AI Anomaly Detection Lead
*Responsible for invoice execution, bank reconciliation, contract verification, and AI insights.*
- **Automated Billing Runs**: Batch execution engine for recurring invoice generation with dunning retry tracking.
- **Bank Statement Reconciliation**: CSV bank parser matching transactions against outstanding balances (Matched, Unmatched, Potential Duplicate).
- **Contract-to-Bill Value Verification**: Cross-references contracted SLA commitments against actual monitored delivery, flagging breaches and issuing credit adjustments.
- **AI Copilot & Anomaly Detection (`/ai/assistant/chat`)**: Identifies billing anomalies, abnormal discounts, and revenue risks through natural language queries.
- **Tamper-Evident Audit Ledger**: Chronological SHA-256 hash chains verifying data integrity with one-click cryptographic verification.

### Role 4: Frontend Architect & UI/UX Developer
*Responsible for the complete web application, persona switching, data visualizations, and customer portal.*
- **Enterprise SaaS Dashboard**: Built with React 18, TypeScript, Vite 6, and Tailwind CSS.
- **Dynamic Role Simulator**: Quick toggle between **Admin**, **Staff**, and **Customer Portal** for frictionless multi-persona evaluation.
- **15 Admin/Staff Modules**: Complete workflows for Dashboard KPIs, Customers, Products, Plans, Quotations, Subscriptions, Digital Twin, Billing Runs, Invoices, Payments, Bank Reconciliation, Verification, AI Insights, Audit Trail, and Settings.
- **8 Customer Portal Views**: Self-service portal for active subscriptions, invoices, online payments, SLA meters, billing disputes, and AI customer support.
- **Data Visualizations**: Recharts Area, Bar, Line, and Donut charts for MRR, velocity, payment inflow, and invoice health distribution.

---

## User Personas & Role-Based Access Control (RBAC)

VERISUB implements backend-enforced, role-based authorization across three distinct personas:

| Capability / Module | ADMIN | STAFF | CUSTOMER |
| :--- | :---: | :---: | :---: |
| **Organization Management & Settings** | Full Access | Read-Only | Denied |
| **Staff User Provisioning (`POST /users/staff`)** | Allowed | Denied | Denied |
| **Customer Directory & Creation** | Full Access | Full Access | Denied |
| **Product & Plan Catalog Management** | Full Access | Operational | Denied |
| **Quotation Drafting & Conversion** | Full Access | Full Access | Denied |
| **Subscription Lifecycle (Pause, Resume, Renew)** | Full Access | Full Access | Self-Service Requests |
| **Subscription Digital Twin Telemetry** | Full Access | Full Access | Denied |
| **Billing Runs & Batch Invoice Execution** | Full Access | Execute Allowed | Denied |
| **Payment Recording & Bank Reconciliation** | Full Access | Operational | Denied |
| **SLA Verification & Credit Approval** | Full Access | View Only | Denied |
| **AI Anomaly Copilot (`/ai-insights`)** | Full Access | Full Access | Denied |
| **Cryptographic Audit Log & Verification** | Full Access | View Only | Denied |
| **Customer Portal (My Subs, Invoices, Pay)** | Switchable | Switchable | Dedicated Portal |
| **SLA Delivery Meters & Dispute Filing** | View | View | Full Access |

---

## Technology Stack

### Backend
- **Python 3.10+**
- **FastAPI**: Asynchronous web API framework
- **SQLAlchemy 2.0**: Typed mapped columns, relationship constraints, declarative base
- **Pydantic v2**: High-performance validation with `ConfigDict(from_attributes=True)`
- **Alembic**: Database migrations with automated schema detection
- **PostgreSQL / SQLite**: Dual support for production and development/testing
- **Argon2id (`argon2-cffi`)**: Memory-hardened password hashing
- **PyJWT**: JSON Web Token issuance, claims verification, and token rotation
- **Decimal Precision**: Zero floating-point math across all financial entities

### Frontend
- **React 18 + TypeScript**: Type-safe component architecture
- **Vite 6**: Ultra-fast module bundling and hot module replacement
- **Tailwind CSS**: Enterprise slate & zinc palette with customized indigo accent (`#4f46e5`)
- **TanStack React Query v5**: Server-state synchronization, optimistic mutations, cache invalidation
- **React Router v6**: Declarative client-side routing with role-based route guards
- **Recharts**: Responsive financial charts (MRR Area, Inflow Line, Velocity Bar, Health Donut)
- **Framer Motion**: Micro-interactions, modal transitions, and lifecycle progression timeline
- **Lucide React**: Clean iconography

---

## Repository Structure

```text
Subscription-Management-System/
├── app/                                 # Subscription Engine & Core Modules
│   ├── core/
│   │   ├── auth.py                      # Multi-tenant user & organization auth dependencies
│   │   ├── config.py                    # Environment settings via Pydantic
│   │   ├── database.py                  # SQLAlchemy engine, session maker, Base
│   │   └── exceptions.py                # Domain exception handlers
│   └── modules/
│       ├── billing/                     # Invoices, payments, tax discount interfaces
│       ├── customers/                   # Customer business records & history
│       ├── plans/                       # Billing plans & price revision history
│       ├── products/                    # Products & variants with Decimal pricing
│       ├── quotations/                  # Quotes with price snapshots & conversion
│       └── subscriptions/               # Lifecycle machine, Digital Twin, Impact Analysis
│   └── main.py                          # Subscription Engine FastAPI application
├── backend/                             # Database & Auth Foundation (Member 1)
│   ├── alembic/                         # Alembic migrations for foundational tables
│   │   ├── env.py
│   │   └── versions/                    # Initial schema migration
│   ├── app/
│   │   ├── core/                        # Argon2id security, JWT, RBAC permissions
│   │   ├── db/                          # Base declarative and session management
│   │   ├── dependencies/                # Reusable FastAPI auth dependencies
│   │   ├── models/                      # 13 relational models (Org, User, Customer, Tokens)
│   │   ├── routers/                     # Auth, Org, User, Customer REST routers
│   │   ├── schemas/                     # Pydantic v2 request/response schemas
│   │   └── services/                    # Business services layer
│   ├── tests/                           # 57 automated tests for Auth, RBAC & Isolation
│   ├── requirements.txt                 # Backend dependencies
│   └── .env.example                     # Environment configuration template
├── frontend/                            # React 18 + Vite Commercial Web Application
│   ├── src/
│   │   ├── components/                  # Common UI components (Card, Modal, Table, etc.)
│   │   │   └── layout/                  # Sidebar, TopNav, AppLayout, CustomerLayout
│   │   ├── features/                    # 17 Feature modules (Auth, Dashboard, Subs, etc.)
│   │   ├── services/                    # Axios API client, query stores, fallback data
│   │   └── types/                       # Comprehensive TypeScript domain interfaces
│   ├── package.json
│   ├── tailwind.config.js
│   └── vite.config.ts
├── tests/                               # 19 automated tests for Subscription Engine
├── alembic/                             # Root migrations
├── requirements.txt                     # Root Python dependencies
├── package.json                         # Workspace root package scripts
├── API_DOCUMENTATION.md                 # Detailed REST endpoint specification
└── CONTRIBUTIONS.md                     # Consolidated engineering deliverables log
```

---

## Getting Started & Local Setup

### Prerequisites
- **Python 3.10+**
- **Node.js 18+ & npm**
- **Git**

---

### Backend Setup

1. **Clone the repository and switch to the assigned branch**:
   ```bash
   git clone https://github.com/Akshaya2720/Subscription-Management-System.git
   cd Subscription-Management-System
   ```

2. **Create and activate a Python virtual environment**:
   ```bash
   # On Windows (PowerShell):
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1

   # On Linux / macOS:
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   Create a `.env` file from `.env.example`:
   ```bash
   cp backend/.env.example backend/.env
   ```
   *(For development, SQLite is supported out of the box with `DATABASE_URL=sqlite:///./verisub.db`)*

5. **Run Database Migrations**:
   ```bash
   # From the backend directory:
   cd backend
   python -m alembic upgrade head
   cd ..
   ```

6. **Start the FastAPI Backend Server**:
   ```bash
   python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
   ```

   - **Interactive Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
   - **ReDoc Documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
   - **Health Check**: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

---

### Frontend Setup

1. **Navigate to the frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install Node packages**:
   ```bash
   npm install
   ```

3. **Configure API target** (optional):
   Verify `frontend/.env` contains:
   ```env
   VITE_API_URL=http://localhost:8000/api/v1
   ```

4. **Start the Vite development server**:
   ```bash
   npm run dev
   ```
   Open [http://localhost:5173](http://localhost:5173) in your browser.

5. **Demo Persona Switcher**:
   In the application header, use the quick-switcher pills to instantly toggle between **Admin**, **Staff**, and **Customer Portal** personas.

---

## API Endpoints Reference

All endpoints are versioned under `/api/v1/`.

### 1. Authentication (`/api/v1/auth`)
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :---: |
| `POST` | `/auth/register` | Register new organization and initial Admin | No |
| `POST` | `/auth/login` | Authenticate with email/password, returns JWT pair | No |
| `POST` | `/auth/refresh` | Rotate refresh token and obtain new access token | No |
| `POST` | `/auth/logout` | Revoke active refresh token in database | No |
| `POST` | `/auth/forgot-password` | Generate reset token (dev fallback when no SMTP) | No |
| `POST` | `/auth/reset-password` | Verify token and update password hash | No |
| `GET` | `/auth/me` | Retrieve authenticated user profile & memberships | Yes |
| `PATCH` | `/auth/me` | Update personal user profile | Yes |
| `POST` | `/auth/change-password` | Re-verify current password and update | Yes |

### 2. Organization Management (`/api/v1/organizations`)
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :---: |
| `POST` | `/organizations` | Create an additional tenant organization (assigned ADMIN) | Yes |
| `GET` | `/organizations/current` | Retrieve active tenant profile | Yes (`Membership`) |
| `PATCH` | `/organizations/current` | Update tenant details | Yes (`MANAGE_ORGANIZATION`) |
| `GET` | `/organizations/current/settings` | Get currency, timezone, tax, billing configs | Yes (`MANAGE_SETTINGS`) |
| `PATCH` | `/organizations/current/settings` | Update organization settings | Yes (`MANAGE_SETTINGS`) |

### 3. Users & Staff (`/api/v1/users`)
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :---: |
| `GET` | `/users` | Paginated organization staff listing | Yes (`MANAGE_STAFF`) |
| `POST` | `/users/staff` | Create new staff user account | Yes (`MANAGE_STAFF`, Admin) |
| `GET` | `/users/{id}` | Retrieve specific staff details | Yes (`MANAGE_STAFF`) |
| `PATCH` | `/users/{id}` | Update staff attributes | Yes (`MANAGE_STAFF`) |
| `DELETE` | `/users/{id}` | Deactivate staff membership | Yes (`MANAGE_STAFF`) |

### 4. Customers (`/api/v1/customers`)
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :---: |
| `POST` | `/customers` | Create tenant-scoped customer record | Yes (`MANAGE_CUSTOMERS`) |
| `GET` | `/customers` | Paginated customer search and status filter | Yes (`MANAGE_CUSTOMERS`) |
| `GET` | `/customers/{id}` | Get customer by UUID with addresses & contacts | Yes (`MANAGE_CUSTOMERS`) |
| `PATCH` | `/customers/{id}` | Update customer details | Yes (`MANAGE_CUSTOMERS`) |
| `DELETE` | `/customers/{id}` | Soft-delete customer (sets status to inactive) | Yes (`MANAGE_CUSTOMERS`) |
| `POST` | `/customers/{id}/addresses`| Add billing or shipping address | Yes (`MANAGE_CUSTOMERS`) |
| `POST` | `/customers/{id}/contacts` | Add customer point of contact | Yes (`MANAGE_CUSTOMERS`) |

### 5. Products, Plans, Quotes & Subscriptions
*(Refer to [`API_DOCUMENTATION.md`](file:///D:/Works/odoo/Subscription-Management-System/API_DOCUMENTATION.md) for detailed payloads and models)*
- `POST|GET /api/v1/products`: Product and variant pricing management.
- `POST|GET /api/v1/plans`: Billing frequencies, pause policies, and price history tracking.
- `POST|GET /api/v1/quotations`: Draft quotations, tax calculations, and 1-click subscription conversion.
- `GET /api/v1/subscriptions/{id}/digital-twin`: Live telemetry contract digital twin.
- `POST /api/v1/change-impact/product` & `plan`: Catalog revision revenue simulation.

---

## Automated Testing & Verification

Both the backend and frontend maintain 100% automated test suites.

### Backend Test Suites (76 / 76 Passed)

```bash
# Run Database, Auth & RBAC Suite (Member 1):
pytest backend/tests/ -v

# Run Subscription Engine Suite (Member 2):
pytest tests/ -v
```

**Results:**
- `backend/tests/test_auth.py`: **26 passed** (Registration, password complexity, login, refresh rotation, logout, reset flow, profile, password change)
- `backend/tests/test_rbac.py`: **17 passed** (Org creation, admin privileges, staff limits, customer isolation, forged header protection)
- `backend/tests/test_customer.py`: **14 passed** (Customer CRUD, duplicate code rejection, pagination, search, soft-delete)
- `tests/test_*.py`: **19 passed** (Customers, products, variants, plans, quotations, lifecycle, digital twin, impact analysis, org isolation)

### Frontend Test Suite (15 / 15 Passed)

```bash
cd frontend
npm run test
```

**Results:**
- `auth.test.ts`: Persona switching, JWT storage, protected routes
- `customer.test.ts`: Directory filtering, modal validations, customer state
- `subscription.test.ts`: Lifecycle pause/resume, digital twin telemetry
- `verification.test.ts`: SLA breach detection, service credit approval
- `quotation.test.ts`: Authoritative tax calculations, subscription conversion
- `components.test.tsx`: Common UI button, badge, and stat card components

---

## License

This project is proprietary and confidential — developed for VERISUB Hackathon & Commercial Subscription Verification Platform.
