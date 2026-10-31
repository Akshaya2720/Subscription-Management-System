import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_, func

from app.modules.billing.models import Invoice, InvoiceItem, InvoiceAnomaly, Payment
from app.modules.subscriptions.models import Subscription


class AnomalyDetectionService:
    @staticmethod
    def detect_anomalies_for_invoice(
        db: Session,
        organization_id: uuid.UUID,
        invoice_id: uuid.UUID,
    ) -> List[InvoiceAnomaly]:
        """
        Scan a specific invoice against deterministic financial integrity rules:
        - Duplicate detection
        - Mathematical tax correctness
        - Unusual discounts (> 50% of subtotal)
        - Historical recurring jump comparison
        - Payment over-allocation mismatch
        """
        invoice = (
            db.query(Invoice)
            .filter(Invoice.id == invoice_id, Invoice.organization_id == organization_id)
            .first()
        )
        if not invoice:
            return []

        anomalies: List[InvoiceAnomaly] = []

        # 1. Tax calculation check: Verify mathematical consistency
        expected_taxable = max(Decimal("0.00"), invoice.subtotal - invoice.discount_total)
        if invoice.subtotal > Decimal("0.00") and invoice.tax_total > Decimal("0.00"):
            # Check if tax is reasonably proportional
            effective_tax_rate = (invoice.tax_total / expected_taxable) if expected_taxable > 0 else Decimal("0.00")
            if effective_tax_rate > Decimal("0.40"):  # Extreme tax rate > 40%
                anomalies.append(
                    InvoiceAnomaly(
                        id=uuid.uuid4(),
                        organization_id=organization_id,
                        invoice_id=invoice.id,
                        anomaly_type="INCORRECT_TAX_CALCULATION",
                        severity="HIGH",
                        detected_value=f"Effective tax rate: {effective_tax_rate * 100:.1f}%",
                        expected_value="Standard tax rate <= 28%",
                        explanation=f"Tax total ({invoice.tax_total}) represents an unusually high proportion ({effective_tax_rate * 100:.1f}%) of the taxable base ({expected_taxable}).",
                        detection_method="RULE_BASED",
                        status="DETECTED",
                        created_at=datetime.now(timezone.utc),
                    )
                )

        # 2. Unusual discount check (> 50% of subtotal)
        if invoice.subtotal > Decimal("0.00") and invoice.discount_total > Decimal("0.00"):
            discount_ratio = invoice.discount_total / invoice.subtotal
            if discount_ratio > Decimal("0.50"):
                anomalies.append(
                    InvoiceAnomaly(
                        id=uuid.uuid4(),
                        organization_id=organization_id,
                        invoice_id=invoice.id,
                        anomaly_type="UNUSUAL_DISCOUNT",
                        severity="MEDIUM",
                        detected_value=f"Discount ratio: {discount_ratio * 100:.1f}% ({invoice.discount_total})",
                        expected_value="Standard commercial discount <= 50%",
                        explanation=f"Discount of {invoice.discount_total} exceeds 50% of invoice subtotal ({invoice.subtotal}).",
                        detection_method="RULE_BASED",
                        status="DETECTED",
                        created_at=datetime.now(timezone.utc),
                    )
                )

        # 3. Duplicate invoice detection
        potential_dups = (
            db.query(Invoice)
            .filter(
                Invoice.organization_id == organization_id,
                Invoice.customer_id == invoice.customer_id,
                Invoice.id != invoice.id,
                Invoice.total_amount == invoice.total_amount,
                func.abs(func.julianday(Invoice.issue_date) - func.julianday(invoice.issue_date)) <= 1,
            )
            .all()
        )
        if potential_dups:
            dup_nums = ", ".join(d.invoice_number for d in potential_dups)
            anomalies.append(
                InvoiceAnomaly(
                    id=uuid.uuid4(),
                    organization_id=organization_id,
                    invoice_id=invoice.id,
                    anomaly_type="DUPLICATE_INVOICE",
                    severity="CRITICAL",
                    detected_value=f"Duplicate amount {invoice.total_amount}",
                    expected_value=f"Unique charge per billing cycle",
                    explanation=f"Identical invoice amount ({invoice.total_amount}) issued to the same customer on/around {invoice.issue_date} (Matching invoice: {dup_nums}).",
                    detection_method="RULE_BASED",
                    status="DETECTED",
                    created_at=datetime.now(timezone.utc),
                )
            )

        # 4. Sudden increase in recurring charges comparison
        if invoice.subscription_id:
            prior_invoices = (
                db.query(Invoice)
                .filter(
                    Invoice.organization_id == organization_id,
                    Invoice.subscription_id == invoice.subscription_id,
                    Invoice.id != invoice.id,
                    Invoice.issue_date < invoice.issue_date,
                )
                .order_by(Invoice.issue_date.desc())
                .limit(5)
                .all()
            )
            if prior_invoices:
                last_inv = prior_invoices[0]
                if last_inv.total_amount > Decimal("0.00"):
                    increase_ratio = (invoice.total_amount - last_inv.total_amount) / last_inv.total_amount
                    if increase_ratio > Decimal("0.40"):  # > 40% jump
                        # Check line items to formulate an explainable cause
                        prior_item_count = len(last_inv.items)
                        curr_item_count = len(invoice.items)
                        explanation_detail = ""
                        if curr_item_count > prior_item_count:
                            explanation_detail = f" because additional items/variants were added ({curr_item_count} items vs {prior_item_count} in previous cycle)."
                        else:
                            explanation_detail = f" without an increase in item quantity."

                        anomalies.append(
                            InvoiceAnomaly(
                                id=uuid.uuid4(),
                                organization_id=organization_id,
                                invoice_id=invoice.id,
                                anomaly_type="SUDDEN_INCREASE_CHARGES",
                                severity="MEDIUM",
                                detected_value=f"{increase_ratio * 100:.1f}% increase ({invoice.total_amount})",
                                expected_value=f"Prior recurring level: {last_inv.total_amount}",
                                explanation=f"Invoice amount is {increase_ratio * 100:.1f}% higher than previous cycle ({last_inv.invoice_number} at {last_inv.total_amount}){explanation_detail}",
                                detection_method="RULE_BASED",
                                status="DETECTED",
                                created_at=datetime.now(timezone.utc),
                            )
                        )

                # 5. Optional scikit-learn IsolationForest if >= 5 historical records exist
                if len(prior_invoices) >= 4:
                    try:
                        from sklearn.ensemble import IsolationForest
                        import numpy as np

                        amounts = [float(p.total_amount) for p in prior_invoices]
                        X = np.array(amounts).reshape(-1, 1)
                        model = IsolationForest(contamination=0.1, random_state=42)
                        model.fit(X)
                        pred = model.predict(np.array([[float(invoice.total_amount)]]))
                        if pred[0] == -1 and invoice.total_amount > max(Decimal(str(a)) for a in amounts):
                            anomalies.append(
                                InvoiceAnomaly(
                                    id=uuid.uuid4(),
                                    organization_id=organization_id,
                                    invoice_id=invoice.id,
                                    anomaly_type="UNUSUAL_AMOUNT",
                                    severity="LOW",
                                    detected_value=str(invoice.total_amount),
                                    expected_value=f"Historical cluster [{min(amounts):.2f} - {max(amounts):.2f}]",
                                    explanation=f"Machine learning anomaly detector (IsolationForest trained on {len(amounts)} historical invoices) identified amount as a statistical outlier.",
                                    detection_method="ML_ISOLATION_FOREST",
                                    status="DETECTED",
                                    created_at=datetime.now(timezone.utc),
                                )
                            )
                    except Exception:
                        pass  # Fail gracefully if ML library or shape has issue

        # 6. Payment mismatch
        if invoice.amount_paid > invoice.total_amount:
            anomalies.append(
                InvoiceAnomaly(
                    id=uuid.uuid4(),
                    organization_id=organization_id,
                    invoice_id=invoice.id,
                    anomaly_type="PAYMENT_MISMATCH",
                    severity="HIGH",
                    detected_value=f"Paid {invoice.amount_paid} > Total {invoice.total_amount}",
                    expected_value=f"Paid amount <= {invoice.total_amount}",
                    explanation=f"Overpayment detected: allocated payments ({invoice.amount_paid}) exceed invoice grand total ({invoice.total_amount}).",
                    detection_method="RULE_BASED",
                    status="DETECTED",
                    created_at=datetime.now(timezone.utc),
                )
            )

        # Persist detected anomalies
        for a in anomalies:
            # Check if identical anomaly already logged
            exists = (
                db.query(InvoiceAnomaly)
                .filter(
                    InvoiceAnomaly.invoice_id == invoice.id,
                    InvoiceAnomaly.anomaly_type == a.anomaly_type,
                )
                .first()
            )
            if not exists:
                db.add(a)

        db.commit()
        return (
            db.query(InvoiceAnomaly)
            .filter(InvoiceAnomaly.invoice_id == invoice.id)
            .all()
        )

    @staticmethod
    def run_batch_detection(
        db: Session, organization_id: uuid.UUID
    ) -> List[InvoiceAnomaly]:
        recent_invoices = (
            db.query(Invoice)
            .filter(Invoice.organization_id == organization_id)
            .order_by(Invoice.created_at.desc())
            .limit(100)
            .all()
        )
        all_detected = []
        for inv in recent_invoices:
            anoms = AnomalyDetectionService.detect_anomalies_for_invoice(
                db, organization_id, inv.id
            )
            all_detected.extend(anoms)
        return all_detected

    @staticmethod
    def review_anomaly(
        db: Session,
        organization_id: uuid.UUID,
        anomaly_id: uuid.UUID,
        decision: str,  # RESOLVED, FALSE_POSITIVE
        reviewed_by: uuid.UUID,
    ) -> Optional[InvoiceAnomaly]:
        anomaly = (
            db.query(InvoiceAnomaly)
            .filter(
                InvoiceAnomaly.id == anomaly_id,
                InvoiceAnomaly.organization_id == organization_id,
            )
            .first()
        )
        if not anomaly:
            return None
        anomaly.status = decision.upper()
        anomaly.reviewed_by = reviewed_by
        anomaly.reviewed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(anomaly)
        return anomaly
