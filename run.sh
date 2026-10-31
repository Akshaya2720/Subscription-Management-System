#!/usr/bin/env bash
# ==============================================================================
# VERISUB — Automated Hackathon Demo Launcher & Presenter Script
# ==============================================================================

set -e

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_DIR"

echo "======================================================================"
echo "  🚀 Starting VERISUB Platform for Screen Recording & Evaluation"
echo "======================================================================"

# 1. Kill any stale processes on ports 8000 and 3000
echo "[1/4] Freeing ports 8000 and 3000..."
pkill -f "uvicorn app.main:app" 2>/dev/null || true
pkill -f "vite --host" 2>/dev/null || true
sleep 1

# 2. Start FastAPI Backend Daemon
echo "[2/4] Launching FastAPI Backend (Port 8000)..."
nohup "$REPO_DIR/.venv/bin/uvicorn" app.main:app --host 0.0.0.0 --port 8000 < /dev/null > /tmp/uvicorn.log 2>&1 &
BACKEND_PID=$!
echo "      Backend PID: $BACKEND_PID"

# Wait for backend health check
until curl -s http://localhost:8000/health > /dev/null; do
    echo "      Waiting for backend to initialize..."
    sleep 1
done
echo "      ✓ Backend is HEALTHY at http://localhost:8000"

# 3. Start Vite Frontend Daemon
echo "[3/4] Launching Vite Frontend (Port 3000)..."
cd "$REPO_DIR/frontend"
nohup ./node_modules/.bin/vite --host 0.0.0.0 --port 3000 < /dev/null > /tmp/vite.log 2>&1 &
FRONTEND_PID=$!
echo "      Frontend PID: $FRONTEND_PID"

# Wait for frontend HTTP response
until curl -s http://localhost:3000 > /dev/null; do
    echo "      Waiting for frontend to initialize..."
    sleep 1
done
echo "      ✓ Frontend is READY at http://localhost:3000"

# 4. Open in Safari / Default Browser
echo "[4/4] Opening browser to http://localhost:3000..."
open "http://localhost:3000" || true

echo ""
echo "======================================================================"
echo "  🎬 PRESENTATION RECORDING SCRIPT (READ THIS DURING RECORDING)"
echo "======================================================================"
echo ""
echo "  [0:00 - 0:30] TOP NAVIGATION & PERSONA SWITCHING"
echo "  • Say: \"Welcome to VERISUB, our Intelligent Subscription and Billing Verification Platform.\""
echo "  • Action: Point mouse to top-right green badge: 'NODE LIVE | 32ms | 99.98% SLA'."
echo "  • Action: Click Role Switcher dropdown ('ADMIN' ↔ 'STAFF' ↔ 'CUSTOMER')."
echo "  • Say: \"We fuse Apple's minimal layout with Paddle's SaaS cards and Solana PublicNode's"
echo "          live RPC infrastructure telemetry. Evaluators can switch roles in 1 click.\""
echo ""
echo "  [0:30 - 1:00] EXECUTIVE FINANCE DASHBOARD"
echo "  • Say: \"Our dashboard computes metrics across 5,000 invoices and 1,000 subscriptions"
echo "          in under 95ms using single-pass SQL aggregations.\""
echo "  • Action: Hover over MRR ($128k), Revenue ($1.65M), and the Revenue Velocity chart."
echo ""
echo "  [1:00 - 1:30] CATALOG VARIANTS & PLAN FLAGS"
echo "  • Action: Click 'Products & Plans' in the left menu."
echo "  • Action: Highlight the '+ $560.00 Odoo Brand' variant badge."
echo "  • Action: Click 'Plans' tab and highlight the 4 flags: [Pausable], [Renewable], [Early Close], [Auto-Close]."
echo "  • Say: \"Products support additive pricing deltas, and plans feature 4 discrete database flags.\""
echo ""
echo "  [1:30 - 2:05] QUOTATIONS, LIFECYCLE & DIGITAL TWIN"
echo "  • Action: Click 'Subscriptions' in the menu -> Click any subscription to open 'Digital Twin'."
echo "  • Action: Click 'Pause Subscription' -> enter reason -> confirm (turns PAUSED)."
echo "  • Action: Click 'Resume Subscription' (turns ACTIVE)."
echo "  • Say: \"Quotations freeze pricing snapshots. The Digital Twin combines contract terms,"
echo "          live billing state, and event history backed by an authoritative state machine.\""
echo ""
echo "  [2:05 - 2:35] AUTOMATED BILLING & PAYMENT GATEWAY"
echo "  • Action: Click 'Billing & Invoices' in the menu -> Click an invoice for printable layout."
echo "  • Action: Click 'Pay with Gateway' -> choose Card/UPI -> click 'Authorize Payment' (turns PAID)."
echo "  • Say: \"Recurring billing runs are idempotent with unique constraints preventing double billing."
echo "          Invoices format into printable tax documents with instant gateway reconciliation.\""
echo ""
echo "  [2:35 - 3:05] SLA VERIFICATION & SHA-256 BLOCKCHAIN AUDIT"
echo "  • Action: Click 'Value Verification' in the menu."
echo "  • Action: Show SLA telemetry table (contract SLA vs actual uptime, proposed credit)."
echo "  • Action: Scroll down to Cryptographic Audit Trail (current_hash & previous_hash chained to Genesis)."
echo "  • Say: \"Our core innovation verifies live service telemetry against contract SLAs,"
echo "          automatically computing service credits upon breach. All events are sealed in a"
echo "          tamper-evident SHA-256 blockchain ledger. Thank you!\""
echo ""
echo "======================================================================"
echo "  To stop the servers later, run:  pkill -f uvicorn; pkill -f vite"
echo "======================================================================"
