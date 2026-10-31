# VERISUB - Subscription Management System

VERISUB manages the complete subscription lifecycle for modern software businesses.

---

## Technology Stack

- **Python**: 3.9+
- **FastAPI**: Modern, async web framework for building APIs
- **SQLAlchemy 2.0**: Next-generation Python ORM
- **Pydantic 2**: High-performance data validation and serialization
- **PostgreSQL / SQLite**: Relational database storage with UUID primary keys
- **Alembic**: Database migrations
- **Decimal**: Strict monetary precision across all financial fields (no floating-point rounding errors)

---

## Directory Structure

```text
├── app/
│   ├── core/
│   │   ├── auth.py          # Member 1 Foundation: Organization, User, Auth dependencies
│   │   ├── config.py        # Settings via Pydantic Settings
│   │   ├── database.py      # SQLAlchemy 2.0 engine, Base, and session dependency
│   │   └── exceptions.py    # Standard domain exception handlers
│   ├── modules/
│   │   ├── customers/       # Customer CRUD, search, pagination, invoices/subs history
│   │   ├── products/        # Products and Variants CRUD with Decimal pricing
│   │   ├── plans/           # Subscription Plans with frequency validation & price history
│   │   ├── quotations/      # Quotations with price snapshots, expiry & conversion
│   │   ├── subscriptions/   # Lifecycle state machine, Digital Twin, Change Impact Analysis
│   │   └── billing/         # Member 3 Coordination: Invoice, Payment models & tax interfaces
│   └── main.py              # Application entrypoint registering all /api/v1/ routes
├── alembic/                 # Migration scripts
├── tests/                   # 19 automated integration and unit tests
├── requirements.txt         # Project dependencies
├── API_DOCUMENTATION.md     # Detailed API endpoints reference
└── CONTRIBUTIONS.md         # Deliverables, architecture, and verification report
```

---

## Quickstart

### 1. Environment Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Database Migrations

```bash
alembic upgrade head
```

### 3. Run Application Server

```bash
uvicorn app.main:app --reload --port 8000
```

- Interactive OpenAPI Swagger UI: `http://localhost:8000/docs`
- ReDoc UI: `http://localhost:8000/redoc`

### 4. Run Test Suite

```bash
pytest -v
```

---

## Key Features

1. **Multi-Tenant Scoping**: All operations require an organization context (`X-Organization-Id` header) to ensure strict isolation.
2. **Immutable Price Snapshots**: Quotations and subscriptions freeze unit prices at agreement time. Subsequent catalog price updates never alter active contracts.
3. **Strict Lifecycle State Machine**: Enforces valid transitions (`DRAFT` → `CONFIRMED` → `ACTIVE` → `PAUSED` → `ACTIVE` → `CLOSED`), disallowing invalid activations or resumes.
4. **Subscription Digital Twin**: Endpoint `/api/v1/subscriptions/{id}/digital-twin` combines real database records from Customer, Plan, Items, Quotations, Invoices, Payments, and Audit Events.
5. **Change Impact Analysis**: Previews the revenue, subscription, and quotation impact of planned product/plan price revisions without modifying customer contracts.
