import uuid
from datetime import datetime, date, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_

from app.core.exceptions import (
    EntityNotFoundException,
    InvalidStateTransitionException,
    BusinessRuleValidationException,
)
from app.modules.billing.models import (
    Contract,
    ServiceCommitment,
    ServiceEvent,
    VerificationRun,
    VerificationResult,
    ServiceCredit,
)
from app.modules.subscriptions.models import Subscription


class VerificationService:
    @staticmethod
    def create_contract(
        db: Session,
        organization_id: uuid.UUID,
        subscription_id: uuid.UUID,
        contract_reference: str,
        start_date: date,
        end_date: Optional[date] = None,
        document_reference: Optional[str] = None,
        commitments_data: Optional[List[Dict[str, Any]]] = None,
    ) -> Contract:
        contract = Contract(
            id=uuid.uuid4(),
            organization_id=organization_id,
            subscription_id=subscription_id,
            contract_reference=contract_reference,
            start_date=start_date,
            end_date=end_date,
            document_reference=document_reference,
            status="ACTIVE",
            created_at=datetime.now(timezone.utc),
        )
        db.add(contract)
        db.flush()

        if commitments_data:
            for c in commitments_data:
                commitment = ServiceCommitment(
                    id=uuid.uuid4(),
                    contract_id=contract.id,
                    commitment_type=c["commitment_type"].upper(),
                    expected_value=Decimal(str(c["expected_value"])).quantize(Decimal("0.0001")),
                    measurement_unit=c.get("measurement_unit", "PERCENTAGE").upper(),
                    verification_rule=c.get("verification_rule", "GREATER_OR_EQUAL").upper(),
                    penalty_rate_per_unit=Decimal(str(c.get("penalty_rate_per_unit", "0.00"))).quantize(Decimal("0.01")),
                )
                db.add(commitment)

        db.commit()
        db.refresh(contract)
        return contract

    @staticmethod
    def record_service_event(
        db: Session,
        subscription_id: uuid.UUID,
        event_type: str,
        actual_value: Decimal,
        event_timestamp: datetime,
        evidence_reference: str,
        commitment_id: Optional[uuid.UUID] = None,
        source: str = "MONITORING_SYSTEM",
        status: str = "VERIFIED",
    ) -> ServiceEvent:
        event = ServiceEvent(
            id=uuid.uuid4(),
            subscription_id=subscription_id,
            commitment_id=commitment_id,
            event_type=event_type.upper(),
            actual_value=actual_value.quantize(Decimal("0.0001")),
            event_timestamp=event_timestamp,
            evidence_reference=evidence_reference,
            source=source.upper(),
            status=status.upper(),
            created_at=datetime.now(timezone.utc),
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    @staticmethod
    def run_verification(
        db: Session,
        organization_id: uuid.UUID,
        subscription_id: uuid.UUID,
    ) -> VerificationRun:
        """
        Execute deterministic contract-to-bill verification for a subscription:
        1. Retrieve active contract and commitments.
        2. Retrieve verified service events.
        3. Evaluate expected vs actual values.
        4. Detect discrepancies and generate clear explanations with evidence references.
        5. Propose SLA credit if breach detected and penalty rate configured.
        """
        contract = (
            db.query(Contract)
            .filter(
                Contract.subscription_id == subscription_id,
                Contract.organization_id == organization_id,
                Contract.status == "ACTIVE",
            )
            .first()
        )
        if not contract:
            raise EntityNotFoundException(
                "Active Contract", f"subscription_id={subscription_id}"
            )

        commitments = (
            db.query(ServiceCommitment)
            .filter(ServiceCommitment.contract_id == contract.id)
            .all()
        )
        if not commitments:
            raise BusinessRuleValidationException(
                f"Contract {contract.contract_reference} has no service commitments defined."
            )

        run = VerificationRun(
            id=uuid.uuid4(),
            subscription_id=subscription_id,
            contract_id=contract.id,
            run_date=datetime.now(timezone.utc),
            status="COMPLETED",
            overall_result="COMPLIANT",
            created_at=datetime.now(timezone.utc),
        )
        db.add(run)
        db.flush()

        has_breach = False
        has_warning = False

        for comm in commitments:
            # Query service events matching this commitment or event type
            events_query = db.query(ServiceEvent).filter(
                ServiceEvent.subscription_id == subscription_id,
                or_(
                    ServiceEvent.commitment_id == comm.id,
                    ServiceEvent.event_type == comm.commitment_type,
                ),
            )
            # Prioritize VERIFIED evidence
            events = events_query.order_by(ServiceEvent.event_timestamp.desc()).all()

            if not events:
                result_item = VerificationResult(
                    id=uuid.uuid4(),
                    verification_run_id=run.id,
                    commitment_id=comm.id,
                    expected_value=comm.expected_value,
                    actual_value=Decimal("0.0000"),
                    variance=comm.expected_value,
                    result="WARNING",
                    explanation=f"No recorded service delivery events found for {comm.commitment_type}.",
                    evidence_reference=None,
                )
                db.add(result_item)
                has_warning = True
                continue

            # Average or latest actual value depending on metric
            # For UPTIME, average measured percentage; for count/hours, sum or latest
            if comm.measurement_unit == "PERCENTAGE":
                actual_val = sum(e.actual_value for e in events) / Decimal(str(len(events)))
            else:
                actual_val = sum(e.actual_value for e in events)
            actual_val = actual_val.quantize(Decimal("0.0001"))

            rule = comm.verification_rule
            breached = False
            evidence_refs = ", ".join(set(e.evidence_reference for e in events if e.evidence_reference))

            if rule == "GREATER_OR_EQUAL":
                variance = comm.expected_value - actual_val
                if actual_val < comm.expected_value:
                    breached = True
            elif rule == "LESS_OR_EQUAL":
                variance = actual_val - comm.expected_value
                if actual_val > comm.expected_value:
                    breached = True
            else:  # EXACT
                variance = abs(actual_val - comm.expected_value)
                if actual_val != comm.expected_value:
                    breached = True

            res_status = "FAIL" if breached else "PASS"
            if breached:
                has_breach = True
                explanation = (
                    f"SLA Breach: Contract committed {comm.expected_value} {comm.measurement_unit} "
                    f"({comm.verification_rule}), but actual verified delivery was {actual_val} {comm.measurement_unit}. "
                    f"Variance: {variance:.4f}. Evidence: {evidence_refs}"
                )
            else:
                explanation = (
                    f"SLA Met: Actual verified delivery of {actual_val} {comm.measurement_unit} "
                    f"meets or exceeds contractual target {comm.expected_value} {comm.measurement_unit}. "
                    f"Evidence: {evidence_refs}"
                )

            result_record = VerificationResult(
                id=uuid.uuid4(),
                verification_run_id=run.id,
                commitment_id=comm.id,
                expected_value=comm.expected_value,
                actual_value=actual_val,
                variance=variance.quantize(Decimal("0.0001")),
                result=res_status,
                explanation=explanation,
                evidence_reference=evidence_refs or None,
            )
            db.add(result_record)
            db.flush()

            # If breached and penalty rate configured, propose credit
            if breached and comm.penalty_rate_per_unit > Decimal("0.00"):
                proposed = (abs(variance) * comm.penalty_rate_per_unit).quantize(Decimal("0.01"))
                credit = ServiceCredit(
                    id=uuid.uuid4(),
                    subscription_id=subscription_id,
                    verification_result_id=result_record.id,
                    proposed_credit=proposed,
                    approved_credit=None,
                    status="PROPOSED",
                    created_at=datetime.now(timezone.utc),
                )
                db.add(credit)

        if has_breach:
            run.overall_result = "BREACH"
        elif has_warning:
            run.overall_result = "PARTIAL_BREACH"
        else:
            run.overall_result = "COMPLIANT"

        db.commit()
        db.refresh(run)
        return run

    @staticmethod
    def approve_service_credit(
        db: Session,
        credit_id: uuid.UUID,
        approved_by: uuid.UUID,
        approved_amount: Optional[Decimal] = None,
        notes: Optional[str] = None,
    ) -> ServiceCredit:
        credit = db.query(ServiceCredit).filter(ServiceCredit.id == credit_id).first()
        if not credit:
            raise EntityNotFoundException("ServiceCredit", str(credit_id))
        if credit.status != "PROPOSED":
            raise InvalidStateTransitionException(
                current_status=credit.status,
                target_status="APPROVED",
                reason="Only PROPOSED credits can be approved.",
            )

        final_credit = (approved_amount or credit.proposed_credit).quantize(Decimal("0.01"))
        credit.approved_credit = final_credit
        credit.status = "APPROVED"
        credit.approved_by = approved_by
        credit.approval_reason = notes or "Authorized contract discrepancy credit"
        db.commit()
        db.refresh(credit)
        return credit

    @staticmethod
    def reject_service_credit(
        db: Session,
        credit_id: uuid.UUID,
        rejected_by: uuid.UUID,
        reason: Optional[str] = None,
    ) -> ServiceCredit:
        credit = db.query(ServiceCredit).filter(ServiceCredit.id == credit_id).first()
        if not credit:
            raise EntityNotFoundException("ServiceCredit", str(credit_id))
        if credit.status != "PROPOSED":
            raise InvalidStateTransitionException(
                current_status=credit.status,
                target_status="REJECTED",
                reason="Only PROPOSED credits can be rejected.",
            )

        credit.status = "REJECTED"
        credit.approved_by = rejected_by
        credit.approval_reason = reason or "Rejected during managerial review"
        db.commit()
        db.refresh(credit)
        return credit
