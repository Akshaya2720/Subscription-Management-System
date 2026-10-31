import csv
import io
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_

from app.modules.billing.models import (
    ReconciliationRun,
    ReconciliationItem,
    Payment,
    Invoice,
)


class ReconciliationService:
    @staticmethod
    def parse_csv(csv_content: str) -> List[Dict[str, Any]]:
        """
        Parse CSV content with flexible headers:
        Transaction date / Date / transaction_date
        Reference / Ref / reference
        Description / Desc / description
        Amount / amount
        Currency / currency
        """
        records = []
        reader = csv.DictReader(io.StringIO(csv_content.strip()))
        for row in reader:
            # Normalize keys to lowercase stripped
            cleaned = {k.strip().lower().replace(" ", "_"): v.strip() for k, v in row.items() if k}
            
            raw_date = cleaned.get("transaction_date") or cleaned.get("date") or str(date.today())
            try:
                tx_date = datetime.strptime(raw_date, "%Y-%m-%d").date()
            except Exception:
                try:
                    tx_date = datetime.strptime(raw_date, "%d/%m/%Y").date()
                except Exception:
                    tx_date = date.today()

            ref = cleaned.get("reference") or cleaned.get("ref") or f"TXN-{uuid.uuid4().hex[:8].upper()}"
            desc = cleaned.get("description") or cleaned.get("desc") or "Bank statement item"
            raw_amt = cleaned.get("amount") or "0.00"
            try:
                amt = Decimal(raw_amt.replace(",", "").replace("$", "").replace("₹", "")).quantize(Decimal("0.01"))
            except Exception:
                amt = Decimal("0.00")
            curr = cleaned.get("currency") or "INR"

            records.append({
                "transaction_date": tx_date,
                "reference": ref,
                "description": desc,
                "amount": amt,
                "currency": curr.upper(),
            })
        return records

    @staticmethod
    def process_reconciliation(
        db: Session,
        organization_id: uuid.UUID,
        filename: str,
        records: List[Dict[str, Any]],
    ) -> ReconciliationRun:
        run_ref = f"REC-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M')}-{uuid.uuid4().hex[:6].upper()}"
        run = ReconciliationRun(
            id=uuid.uuid4(),
            organization_id=organization_id,
            run_reference=run_ref,
            imported_at=datetime.now(timezone.utc),
            filename=filename,
            total_records=len(records),
            matched_count=0,
            unmatched_count=0,
            discrepancy_count=0,
            status="PENDING_REVIEW",
        )
        db.add(run)
        db.flush()

        # Query existing payments and invoices for matching
        existing_payments = (
            db.query(Payment)
            .filter(Payment.organization_id == organization_id)
            .all()
        )
        existing_invoices = (
            db.query(Invoice)
            .filter(Invoice.organization_id == organization_id)
            .all()
        )

        matched_c = 0
        unmatched_c = 0
        discrepancy_c = 0

        # Track references seen in this CSV to detect internal duplicates
        seen_refs: Dict[str, int] = {}
        for r in records:
            seen_refs[r["reference"]] = seen_refs.get(r["reference"], 0) + 1

        for r in records:
            tx_ref = r["reference"]
            tx_amt = r["amount"]
            tx_date = r["transaction_date"]
            tx_desc = r["description"].lower()

            matched_payment: Optional[Payment] = None
            matched_invoice: Optional[Invoice] = None
            match_status = "UNMATCHED"
            confidence = Decimal("0.00")
            review_notes = None

            # 1. Check for duplicate statement entry
            if seen_refs.get(tx_ref, 0) > 1:
                match_status = "POTENTIAL_DUPLICATE"
                confidence = Decimal("95.00")
                review_notes = f"Transaction reference '{tx_ref}' appears multiple times in bank statement."
                discrepancy_c += 1

            else:
                # 2. Check for exact match against payments by transaction_reference or payment_reference
                for pay in existing_payments:
                    if (
                        pay.transaction_reference
                        and pay.transaction_reference.strip().lower() == tx_ref.strip().lower()
                    ) or pay.payment_reference.strip().lower() == tx_ref.strip().lower():
                        if pay.amount == tx_amt:
                            matched_payment = pay
                            match_status = "MATCHED"
                            confidence = Decimal("100.00")
                            review_notes = f"Exact match with payment {pay.payment_reference}."
                            break
                        else:
                            matched_payment = pay
                            match_status = "AMOUNT_MISMATCH"
                            confidence = Decimal("75.00")
                            review_notes = f"Reference matches {pay.payment_reference}, but amount differs (Bank: {tx_amt}, Recorded: {pay.amount})."
                            break

                # 3. If no payment matched, check against open invoices (e.g. invoice number mentioned in description or reference)
                if match_status == "UNMATCHED":
                    for inv in existing_invoices:
                        inv_num_clean = inv.invoice_number.strip().lower()
                        if inv_num_clean in tx_desc or inv_num_clean in tx_ref.strip().lower():
                            matched_invoice = inv
                            if inv.total_amount == tx_amt or inv.amount_due == tx_amt:
                                match_status = "MATCHED"
                                confidence = Decimal("92.00")
                                review_notes = f"Invoice number {inv.invoice_number} found in description and amount matches balance."
                            else:
                                match_status = "AMOUNT_MISMATCH"
                                confidence = Decimal("60.00")
                                review_notes = f"Invoice {inv.invoice_number} found in description, but amount {tx_amt} does not match balance due {inv.amount_due}."
                            break

                # 4. If still unmatched, check for ambiguous date & amount match
                if match_status == "UNMATCHED":
                    candidate_payments = [
                        p for p in existing_payments
                        if p.amount == tx_amt
                        and abs((p.payment_date.date() - tx_date).days) <= 2
                    ]
                    if len(candidate_payments) == 1:
                        matched_payment = candidate_payments[0]
                        match_status = "NEEDS_MANUAL_REVIEW"
                        confidence = Decimal("50.00")
                        review_notes = f"Amount and date match payment {matched_payment.payment_reference}, but reference differs. Requires manual review."
                        discrepancy_c += 1
                    elif len(candidate_payments) > 1:
                        match_status = "NEEDS_MANUAL_REVIEW"
                        confidence = Decimal("30.00")
                        review_notes = f"Multiple payments match this amount around {tx_date}. Ambiguous match."
                        discrepancy_c += 1
                    else:
                        match_status = "UNMATCHED"
                        confidence = Decimal("0.00")
                        review_notes = "No matching payment or invoice found."
                        unmatched_c += 1

            if match_status == "MATCHED":
                matched_c += 1

            item = ReconciliationItem(
                id=uuid.uuid4(),
                reconciliation_run_id=run.id,
                transaction_date=tx_date,
                reference=tx_ref,
                description=r["description"],
                amount=tx_amt,
                currency=r["currency"],
                matched_payment_id=matched_payment.id if matched_payment else None,
                matched_invoice_id=matched_invoice.id if matched_invoice else None,
                match_status=match_status,
                confidence_score=confidence,
                review_notes=review_notes,
            )
            db.add(item)

        run.matched_count = matched_c
        run.unmatched_count = unmatched_c
        run.discrepancy_count = discrepancy_c
        if unmatched_c == 0 and discrepancy_c == 0:
            run.status = "COMPLETED"
        else:
            run.status = "PENDING_REVIEW"

        db.commit()
        db.refresh(run)
        return run

    @staticmethod
    def review_reconciliation_item(
        db: Session,
        organization_id: uuid.UUID,
        item_id: uuid.UUID,
        decision: str,  # MATCH, REJECT
        matched_invoice_id: Optional[uuid.UUID] = None,
        notes: Optional[str] = None,
        reviewed_by: Optional[uuid.UUID] = None,
    ) -> Optional[ReconciliationItem]:
        item = (
            db.query(ReconciliationItem)
            .join(ReconciliationRun)
            .filter(
                ReconciliationItem.id == item_id,
                ReconciliationRun.organization_id == organization_id,
            )
            .first()
        )
        if not item:
            return None

        if decision.upper() == "MATCH":
            item.match_status = "MATCHED"
            item.confidence_score = Decimal("100.00")
            if matched_invoice_id:
                item.matched_invoice_id = matched_invoice_id
        elif decision.upper() == "REJECT":
            item.match_status = "UNMATCHED"
        
        item.review_notes = notes or item.review_notes
        item.reviewed_by = reviewed_by
        item.reviewed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(item)
        return item
