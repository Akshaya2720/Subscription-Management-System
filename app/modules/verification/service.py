"""Service layer for deterministic SLA contract verification and SHA-256 tamper-evident audit ledger."""

import json
import uuid
import hashlib
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timezone
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session

from app.core.exceptions import EntityNotFoundException, BusinessRuleValidationException
from app.models.verification import VerificationContract, AuditLog, VerificationStatus
from app.models.billing import Invoice
from app.modules.verification.repository import VerificationRepository, AuditRepository
from app.modules.verification.schemas import (
    VerificationContractCreate,
    SlaEvaluationRequest,
    SlaEvaluationResult,
    AuditChainVerificationResult,
)

GENESIS_HASH = "0" * 64


def _compute_block_hash(
    prev_hash: str,
    seq: int,
    entity_type: str,
    entity_id: str,
    action: str,
    actor_email: str,
    payload_str: str,
    created_at_iso: str,
) -> str:
    raw_material = f"{prev_hash}:{seq}:{entity_type}:{entity_id}:{action}:{actor_email}:{payload_str}:{created_at_iso}"
    return hashlib.sha256(raw_material.encode("utf-8")).hexdigest()


class SlaVerificationService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = VerificationRepository(db)

    def create_contract(self, org_id: uuid.UUID, data: VerificationContractCreate) -> VerificationContract:
        existing = self.repo.get_by_number(org_id, data.contract_number)
        if existing:
            raise BusinessRuleValidationException(f"Contract number '{data.contract_number}' already exists.")

        contract = VerificationContract(
            organization_id=org_id,
            contract_number=data.contract_number,
            subscription_id=data.subscription_id,
            service_name=data.service_name,
            sla_commitment_description=data.sla_commitment_description,
            target_uptime_percentage=data.target_uptime_percentage,
            actual_recorded_telemetry=data.actual_recorded_telemetry,
            breach_detected=False,
            proposed_credit_amount=data.proposed_credit_amount,
            status=VerificationStatus.PENDING_REVIEW,
        )
        return self.repo.save(contract)

    def list_contracts(self, org_id: uuid.UUID) -> List[VerificationContract]:
        return self.repo.list(org_id)

    def evaluate_sla(self, org_id: uuid.UUID, req: SlaEvaluationRequest) -> SlaEvaluationResult:
        contract = self.repo.get_by_id(org_id, req.contract_id)
        if not contract:
            raise EntityNotFoundException("VerificationContract", str(req.contract_id))

        target = contract.target_uptime_percentage
        measured = req.measured_uptime_percentage
        shortfall = max(Decimal("0.00"), target - measured)
        breach_detected = shortfall > Decimal("0.00")

        # Deterministic credit calculation formula
        # 10% invoice credit per 1.0% uptime breach, capped at 100%
        credit_amount = Decimal("0.00")
        if breach_detected:
            penalty_rate = min(Decimal("100.00"), shortfall * Decimal("10.00"))
            base_amount = Decimal("500.00")  # Default base tier SLA value
            if req.invoice_id:
                inv = self.db.query(Invoice).filter(Invoice.organization_id == org_id, Invoice.id == req.invoice_id).first()
                if inv:
                    base_amount = inv.total_amount

            credit_amount = (base_amount * (penalty_rate / Decimal("100.00"))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            # Apply SLA credit to invoice if provided
            if req.invoice_id:
                inv = self.db.query(Invoice).filter(Invoice.organization_id == org_id, Invoice.id == req.invoice_id).first()
                if inv:
                    inv.sla_credit_amount += credit_amount
                    inv.amount_due = max(Decimal("0.00"), inv.amount_due - credit_amount)
                    self.db.flush()

        contract.breach_detected = breach_detected
        contract.actual_recorded_telemetry = (
            f"{measured}% measured ({req.telemetry_window}) vs target {target}%"
        )
        contract.proposed_credit_amount = credit_amount
        contract.status = VerificationStatus.CREDIT_APPROVED if breach_detected else VerificationStatus.VERIFIED_COMPLIANT
        self.db.commit()
        self.db.refresh(contract)

        return SlaEvaluationResult(
            contract_id=contract.id,
            contract_number=contract.contract_number,
            target_uptime_percentage=target,
            measured_uptime_percentage=measured,
            breach_detected=breach_detected,
            outage_shortfall_percent=shortfall,
            proposed_credit_amount=credit_amount,
            adjudication_status=contract.status.value,
            message=(
                f"SLA breach detected ({shortfall}% shortfall). Credit of ${credit_amount} adjudicated."
                if breach_detected
                else "Telemetry compliant with SLA commitments. Zero penalty credits owed."
            ),
        )

    def adjudicate_contract(self, org_id: uuid.UUID, contract_id: uuid.UUID, approve: bool, user_id: uuid.UUID) -> VerificationContract:
        contract = self.repo.get_by_id(org_id, contract_id)
        if not contract:
            raise EntityNotFoundException("VerificationContract", str(contract_id))

        contract.status = VerificationStatus.CREDIT_APPROVED if approve else VerificationStatus.CREDIT_REJECTED
        contract.adjudicated_at = datetime.now(timezone.utc)
        contract.adjudicated_by = user_id
        return self.repo.save(contract)


class AuditService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = AuditRepository(db)

    def log_action(
        self,
        org_id: uuid.UUID,
        entity_type: str,
        entity_id: str,
        action: str,
        actor_email: str,
        payload: dict,
    ) -> AuditLog:
        """Appends an immutable SHA-256 cryptographically chained audit record."""
        latest = self.repo.get_latest_log(org_id)
        if latest is None:
            seq = 1
            prev_hash = GENESIS_HASH
        else:
            seq = latest.sequence_number + 1
            prev_hash = latest.current_hash

        payload_str = json.dumps(payload, sort_keys=True)
        now = datetime.now(timezone.utc)
        now_iso = now.strftime("%Y-%m-%dT%H:%M:%SZ")

        current_hash = _compute_block_hash(
            prev_hash=prev_hash,
            seq=seq,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            actor_email=actor_email,
            payload_str=payload_str,
            created_at_iso=now_iso,
        )

        entry = AuditLog(
            organization_id=org_id,
            sequence_number=seq,
            previous_hash=prev_hash,
            current_hash=current_hash,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            actor_email=actor_email,
            payload_json=payload_str,
            created_at=now,
        )
        return self.repo.append(entry)

    def list_logs(self, org_id: uuid.UUID, limit: int = 50) -> List[AuditLog]:
        return self.repo.list_logs(org_id, limit=limit)

    def verify_chain(self, org_id: uuid.UUID) -> AuditChainVerificationResult:
        """
        Cryptographic verification:
        Re-computes every block hash and validates unbroken chain integrity.
        Detects database tampering, modified rows, or unauthorized alterations.
        """
        blocks = self.repo.get_all_ordered(org_id)
        if not blocks:
            return AuditChainVerificationResult(
                organization_id=org_id,
                total_blocks_verified=0,
                is_valid=True,
                verification_timestamp=datetime.now(timezone.utc),
            )

        expected_prev_hash = GENESIS_HASH
        for idx, block in enumerate(blocks):
            expected_seq = idx + 1
            if block.sequence_number != expected_seq:
                return AuditChainVerificationResult(
                    organization_id=org_id,
                    total_blocks_verified=idx,
                    is_valid=False,
                    tampered_block_sequence=block.sequence_number,
                    error_detail=f"Sequence discontinuity: expected {expected_seq}, found {block.sequence_number}.",
                    verification_timestamp=datetime.now(timezone.utc),
                )

            if block.previous_hash != expected_prev_hash:
                return AuditChainVerificationResult(
                    organization_id=org_id,
                    total_blocks_verified=idx,
                    is_valid=False,
                    tampered_block_sequence=block.sequence_number,
                    error_detail=f"Chain link broken at block {block.sequence_number}: previous_hash does not match parent current_hash.",
                    verification_timestamp=datetime.now(timezone.utc),
                )

            # Recompute hash
            recomputed = _compute_block_hash(
                prev_hash=block.previous_hash,
                seq=block.sequence_number,
                entity_type=block.entity_type,
                entity_id=block.entity_id,
                action=block.action,
                actor_email=block.actor_email,
                payload_str=block.payload_json,
                created_at_iso=block.created_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            )
            if recomputed != block.current_hash:
                return AuditChainVerificationResult(
                    organization_id=org_id,
                    total_blocks_verified=idx,
                    is_valid=False,
                    tampered_block_sequence=block.sequence_number,
                    error_detail=f"Cryptographic hash mismatch at block {block.sequence_number}. Row contents have been altered directly in storage.",
                    verification_timestamp=datetime.now(timezone.utc),
                )

            expected_prev_hash = block.current_hash

        return AuditChainVerificationResult(
            organization_id=org_id,
            total_blocks_verified=len(blocks),
            is_valid=True,
            verification_timestamp=datetime.now(timezone.utc),
        )
