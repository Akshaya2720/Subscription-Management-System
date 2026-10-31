# VERISUB — Hackathon Screen Recording & Video Presentation Script

Use this teleprompter-ready script while screen-recording your browser.

- **URL to open**: `http://localhost:3000`
- **Total Duration**: ~3 minutes
- **Recommended Setup**: Place your browser window on the left side of your screen and this script on the right side.

---

### [0:00 – 0:30] Introduction, Design System & Live Telemetry
**On Screen**: Open `http://localhost:3000`. Show the Top Navigation bar.  
**Action**:
1. Hover your cursor over the top-right green badge: `NODE LIVE | 32ms | 99.98% SLA`.
2. Click the **Persona Switcher** dropdown in the top bar to show `ADMIN`, `STAFF`, and `CUSTOMER`.

**Speaker Words**:
> "Hello evaluators, welcome to **VERISUB**—our Intelligent Subscription and Billing Verification Platform.
> 
> Our design system unites three powerful concepts: **Apple's standard minimal clean layout**, **Paddle's high-contrast fintech billing cards**, and **Solana PublicNode's real-time infrastructure telemetry**.
> 
> In our top navigation bar, you can see live RPC node telemetry continuously pinging latency and contract uptime. Evaluators can switch between Admin, Staff, and Customer personas with a single click to test role-based access control in real time."

---

### [0:30 – 1:00] Executive Finance Dashboard (<95ms Aggregation)
**On Screen**: Dashboard (`/admin/overview`).  
**Action**:
1. Point at the KPI cards: Active Subscriptions (**667**), Revenue Received (**$1.65M**), Outstanding Receivables (**$687k**), and Overdue Invoices (**2,499**).
2. Hover over the **Monthly Revenue Velocity** area chart.
3. Scroll down slightly to show the **Invoices Requiring Attention** table.

**Speaker Words**:
> "Our finance executive dashboard is powered by single-pass SQL aggregations backed by composite database indexes.
> 
> Operating over thousands of active subscriptions and invoices, all metrics compute in just **94 milliseconds**—over 20 times faster than the 2-second hackathon benchmark.
> 
> The dashboard tracks revenue velocity, customer expansion, and automatically surfaces overdue invoices for priority collections."

---

### [1:00 – 1:30] Catalog Variants & Plan Policy Flags
**On Screen**: Click **Products & Plans** in the left navigation.  
**Action**:
1. In the **Products** table, point to the `+ $560.00 Odoo Brand` badge.
2. Click the **Plans** tab. Point to the four flag badges on any plan row: `[Pausable]`, `[Renewable]`, `[Early Close]`, and `[Auto-Close]`.

**Speaker Words**:
> "In our product catalog, products support additive variant pricing. For example, our Odoo Brand variant adds a 560 price delta to the base service price.
> 
> Each subscription plan models discrete operational rules via four database flags: **Pausable**, **Renewable**, **Closable Early**, and **Auto-Close at Term End**, strictly enforcing business rules before any contract is signed."

---

### [1:30 – 2:05] Quotations, Lifecycle Engine & The Digital Twin
**On Screen**: Click **Subscriptions** in the left menu, then click any subscription row.  
**Action**:
1. Walk through the **Subscription Digital Twin** screen: contract pricing snapshot, telemetry uptime, and event history.
2. Click the **Pause Subscription** button -> type `Scheduled maintenance` -> click confirm (status changes to `PAUSED`).
3. Click **Resume Subscription** (status returns to `ACTIVE`).

**Speaker Words**:
> "Quotations freeze line item pricing snapshots upon approval. This ensures future catalog price updates never alter an existing customer's agreed contractual rate.
> 
> In the **Subscription Digital Twin**, team members see the unified truth of each account: agreed contract terms, live billing state, and event history.
> 
> Our backend state machine strictly validates all transitions. Subscriptions can be paused with mandatory audit reasoning and resumed with full audit tracking."

---

### [2:05 – 2:35] Automated Billing Runs, Printable Invoices & Gateway Payment
**On Screen**: Click **Billing & Invoices** in the left menu.  
**Action**:
1. Click an invoice to show the Paddle-style itemized printable tax invoice.
2. Click the blue **Pay with Gateway** button -> simulated payment modal opens.
3. Select **Card / UPI** -> click **Authorize Payment** -> invoice status updates to `PAID`.

**Speaker Words**:
> "Our recurring billing engine automatically generates invoices from active subscriptions on their billing dates.
> 
> A database uniqueness constraint on subscription ID, period start, and period end strictly guarantees that no customer is ever double-billed or skipped.
> 
> Invoices format into clean, printable tax documents with itemized GST breakdowns, and payments can be settled instantly through our simulated payment gateway with automatic reconciliation."

---

### [2:35 – 3:05] Innovation: SLA Telemetry Verification & SHA-256 Audit Blockchain
**On Screen**: Click **Value Verification** in the left menu (`/admin/verification`).  
**Action**:
1. Show the SLA contract telemetry table: contracted uptime (e.g., 99.99%) vs actual delivery (e.g., 99.40%).
2. Point out the **Proposed Service Credit** calculation.
3. Scroll down to the **Cryptographic Audit Trail**: show `Current Hash` and `Previous Hash` chained to the Genesis block.

**Speaker Words**:
> "Our core innovation is **Contract-to-Bill Value Verification**. Live infrastructure telemetry is continuously evaluated against contracted uptime SLAs.
> 
> When an outage breaches the agreed SLA threshold, our verification engine automatically calculates compensatory service credits before invoices are finalized.
> 
> Finally, every billing run, state transition, and payment is sealed in a tamper-evident **SHA-256 blockchain audit ledger**. If any database row is altered, the cryptographic hash chain immediately breaks and alerts the security team.
> 
> Thank you for your time!"

---

### [Optional 15-Second Outro]: Backend OpenAPI Docs
**On Screen**: Switch browser tab to `http://localhost:8000/docs`.  
**Speaker Words**:
> "All 45+ endpoints are fully documented with OpenAPI schemas, protected by thread-safe sliding window rate limiting and Argon2id multi-tenant RBAC, with 100% passing test suites across both backend and frontend."
