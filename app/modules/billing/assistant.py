import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.modules.billing.models import (
    Invoice,
    Payment,
    VerificationRun,
    VerificationResult,
    ServiceCommitment,
    InvoiceAnomaly,
)
from app.modules.customers.models import Customer
from app.modules.subscriptions.models import Subscription


class BusinessAssistantService:
    @staticmethod
    def answer_query(
        db: Session,
        organization_id: uuid.UUID,
        query_text: str,
    ) -> Dict[str, Any]:
        """
        Controlled explainable assistant backend.
        Executes verified, authorized domain queries against real ledger records.
        No arbitrary SQL; strict organization boundary enforcement.
        """
        q = query_text.strip().lower()
        today = date.today()

        # 1. Outstanding amount query
        if "outstanding" in q or "balance due" in q or "receivable" in q:
            result = (
                db.query(
                    func.coalesce(func.sum(Invoice.amount_due), Decimal("0.00")),
                    func.coalesce(func.sum(Invoice.total_amount), Decimal("0.00")),
                    func.count(Invoice.id),
                )
                .filter(
                    Invoice.organization_id == organization_id,
                    Invoice.status.notin_(["CANCELLED", "VOIDED"]),
                )
                .first()
            )
            total_due, total_billed, count = result[0], result[1], result[2]

            overdue_due = (
                db.query(func.coalesce(func.sum(Invoice.amount_due), Decimal("0.00")))
                .filter(
                    Invoice.organization_id == organization_id,
                    Invoice.due_date < today,
                    Invoice.amount_due > Decimal("0.00"),
                    Invoice.status.notin_(["CANCELLED", "VOIDED"]),
                )
                .scalar()
            )

            answer = (
                f"Total outstanding balance across all customer accounts is "
                f"**{total_due:,.2f} INR** across {count} invoices. "
                f"Of this, **{overdue_due:,.2f} INR** is currently past its payment due date."
            )
            return {
                "query": query_text,
                "category": "OUTSTANDING_AMOUNT",
                "answer": answer,
                "data": {
                    "total_outstanding": float(total_due),
                    "total_billed": float(total_billed),
                    "overdue_portion": float(overdue_due),
                    "invoice_count": count,
                },
                "sources": ["Table: invoices (filtered by organization_id)"],
            }

        # 2. Overdue invoices query
        if "overdue" in q:
            overdue_invoices = (
                db.query(Invoice)
                .filter(
                    Invoice.organization_id == organization_id,
                    Invoice.due_date < today,
                    Invoice.amount_due > Decimal("0.00"),
                    Invoice.status.notin_(["CANCELLED", "VOIDED"]),
                )
                .order_by(Invoice.due_date.asc())
                .all()
            )

            if not overdue_invoices:
                answer = "There are currently 0 overdue invoices across the organization. All accounts are up to date."
                data = []
            else:
                total_overdue = sum(inv.amount_due for inv in overdue_invoices)
                items_summary = [
                    f"• **{inv.invoice_number}** ({inv.customer.name if inv.customer else 'Unknown'}): "
                    f"{inv.amount_due:,.2f} {inv.currency} (Due: {inv.due_date})"
                    for inv in overdue_invoices[:10]
                ]
                answer = (
                    f"Identified **{len(overdue_invoices)}** overdue invoice(s) totaling **{total_overdue:,.2f} INR**:\n\n"
                    + "\n".join(items_summary)
                )
                if len(overdue_invoices) > 10:
                    answer += f"\n...and {len(overdue_invoices) - 10} more."

                data = [
                    {
                        "invoice_number": inv.invoice_number,
                        "customer": inv.customer.name if inv.customer else None,
                        "amount_due": float(inv.amount_due),
                        "due_date": str(inv.due_date),
                    }
                    for inv in overdue_invoices
                ]

            return {
                "query": query_text,
                "category": "OVERDUE_INVOICES",
                "answer": answer,
                "data": data,
                "sources": ["Table: invoices (due_date < today, amount_due > 0)"],
            }

        # 3. Subscriptions with unusual billing / anomalies
        if "unusual" in q or "anomal" in q or "discrepan" in q:
            anomalies = (
                db.query(InvoiceAnomaly)
                .filter(
                    InvoiceAnomaly.organization_id == organization_id,
                    InvoiceAnomaly.status == "DETECTED",
                )
                .order_by(InvoiceAnomaly.created_at.desc())
                .limit(10)
                .all()
            )
            if not anomalies:
                answer = "No unresolved billing anomalies or unusual subscription charges detected in the ledger."
                data = []
            else:
                details = [
                    f"• **{a.invoice.invoice_number if a.invoice else 'Invoice'}** [{a.anomaly_type}]: {a.explanation}"
                    for a in anomalies
                ]
                answer = (
                    f"Detected **{len(anomalies)}** active financial anomaly signal(s):\n\n"
                    + "\n".join(details)
                )
                data = [
                    {
                        "anomaly_id": str(a.id),
                        "anomaly_type": a.anomaly_type,
                        "severity": a.severity,
                        "explanation": a.explanation,
                    }
                    for a in anomalies
                ]

            return {
                "query": query_text,
                "category": "BILLING_ANOMALIES",
                "answer": answer,
                "data": data,
                "sources": ["Table: invoice_anomalies"],
            }

        # 4. Customers with unpaid invoices
        if "customer" in q and ("unpaid" in q or "issue" in q or "pay" in q):
            unpaid_invoices = (
                db.query(Invoice)
                .filter(
                    Invoice.organization_id == organization_id,
                    Invoice.amount_due > Decimal("0.00"),
                    Invoice.status.notin_(["CANCELLED", "VOIDED"]),
                )
                .all()
            )
            customers_map: Dict[str, Dict[str, Any]] = {}
            for inv in unpaid_invoices:
                cname = inv.customer.name if inv.customer else "Unknown"
                if cname not in customers_map:
                    customers_map[cname] = {
                        "name": cname,
                        "unpaid_count": 0,
                        "total_due": Decimal("0.00"),
                    }
                customers_map[cname]["unpaid_count"] += 1
                customers_map[cname]["total_due"] += inv.amount_due

            if not customers_map:
                answer = "No customer accounts currently have unpaid invoices."
            else:
                lines = [
                    f"• **{info['name']}**: {info['unpaid_count']} unpaid invoice(s) totaling {info['total_due']:,.2f} INR"
                    for info in sorted(customers_map.values(), key=lambda x: x["total_due"], reverse=True)
                ]
                answer = (
                    f"Found **{len(customers_map)}** customer(s) with outstanding unpaid balances:\n\n"
                    + "\n".join(lines)
                )

            return {
                "query": query_text,
                "category": "CUSTOMER_UNPAID_STATUS",
                "answer": answer,
                "data": [
                    {
                        "customer": info["name"],
                        "unpaid_invoices": info["unpaid_count"],
                        "balance_due": float(info["total_due"]),
                    }
                    for info in customers_map.values()
                ],
                "sources": ["Tables: invoices, customers"],
            }

        # 5. Service commitments not met / SLA breaches
        if "commitment" in q or "sla" in q or "breach" in q:
            breach_results = (
                db.query(VerificationResult)
                .join(VerificationRun)
                .join(Subscription)
                .filter(
                    Subscription.organization_id == organization_id,
                    VerificationResult.result == "FAIL",
                )
                .order_by(VerificationResult.id.desc())
                .limit(10)
                .all()
            )
            if not breach_results:
                answer = "All verified contracts meet or exceed contractual service commitments. Zero SLA breaches recorded."
                data = []
            else:
                lines = [
                    f"• **{vr.commitment.commitment_type if vr.commitment else 'Commitment'}**: {vr.explanation}"
                    for vr in breach_results
                ]
                answer = (
                    f"Identified **{len(breach_results)}** contract service commitment breach(es):\n\n"
                    + "\n".join(lines)
                )
                data = [
                    {
                        "commitment_type": vr.commitment.commitment_type if vr.commitment else None,
                        "expected": float(vr.expected_value),
                        "actual": float(vr.actual_value),
                        "variance": float(vr.variance),
                        "explanation": vr.explanation,
                    }
                    for vr in breach_results
                ]

            return {
                "query": query_text,
                "category": "SLA_BREACHES",
                "answer": answer,
                "data": data,
                "sources": ["Tables: verification_results, service_commitments"],
            }

        # Default summary
        active_subs = (
            db.query(func.count(Subscription.id))
            .filter(Subscription.organization_id == organization_id, Subscription.status == "ACTIVE")
            .scalar()
            or 0
        )
        total_outstanding = (
            db.query(func.coalesce(func.sum(Invoice.amount_due), Decimal("0.00")))
            .filter(Invoice.organization_id == organization_id, Invoice.status.notin_(["CANCELLED", "VOIDED"]))
            .scalar()
        )
        answer = (
            f"VERISUB Financial Assistant status: Active subscriptions: **{active_subs}**. "
            f"Total open receivables: **{total_outstanding:,.2f} INR**. "
            f"You can ask me about: 'outstanding amount', 'overdue invoices', 'unusual billing', 'unpaid customers', or 'SLA commitments'."
        )
        return {
            "query": query_text,
            "category": "GENERAL_SUMMARY",
            "answer": answer,
            "data": {
                "active_subscriptions": active_subs,
                "total_outstanding": float(total_outstanding),
            },
            "sources": ["VERISUB Core Aggregator"],
        }
