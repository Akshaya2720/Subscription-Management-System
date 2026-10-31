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
