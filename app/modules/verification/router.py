"""FastAPI routers for SLA Verification and SHA-256 Audit Trail."""

import uuid
from typing import List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_organization, get_current_user, require_role
from app.models.auth import Organization, User, UserRole
from app.modules.verification.schemas import (
    VerificationContractCreate,
    VerificationContractResponse,
    SlaEvaluationRequest,
    SlaEvaluationResult,
    AuditLogResponse,
    AuditChainVerificationResult,
)
from app.modules.verification.service import SlaVerificationService, AuditService

verification_router = APIRouter(prefix="/verification", tags=["SLA Verification"])
audit_router = APIRouter(prefix="/audit", tags=["Cryptographic Audit Trail"])


# ── SLA Contract Verification Endpoints ─────────────────────────────────────

@verification_router.get("/contracts", response_model=List[VerificationContractResponse])
def list_contracts(
    org: Organization = Depends(get_current_organization),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List SLA verification contracts for the active organization."""
    service = SlaVerificationService(db)
    return service.list_contracts(org.id)


@verification_router.post("/contracts", response_model=VerificationContractResponse, status_code=status.HTTP_201_CREATED)
def create_contract(
    data: VerificationContractCreate,
    org: Organization = Depends(get_current_organization),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.STAFF)),
    db: Session = Depends(get_db),
):
    """Register an SLA commitment contract."""
    service = SlaVerificationService(db)
    return service.create_contract(org.id, data)


@verification_router.post("/contracts/evaluate", response_model=SlaEvaluationResult)
def evaluate_sla(
    req: SlaEvaluationRequest,
    org: Organization = Depends(get_current_organization),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.STAFF)),
    db: Session = Depends(get_db),
):
    """
    Evaluate actual recorded service telemetry against contractual SLA commitments.
    Applies deterministic credit calculation to billing invoice upon breach detection.
    """
    service = SlaVerificationService(db)
    return service.evaluate_sla(org.id, req)


@verification_router.post("/contracts/{contract_id}/adjudicate", response_model=VerificationContractResponse)
def adjudicate_contract(
    contract_id: uuid.UUID,
    approve: bool = Query(...),
    org: Organization = Depends(get_current_organization),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    """Adjudicate and finalize SLA credit status. ADMIN only."""
    service = SlaVerificationService(db)
    return service.adjudicate_contract(org.id, contract_id, approve=approve, user_id=current_user.id)


# ── Cryptographic Audit Trail Endpoints ─────────────────────────────────────

@audit_router.get("/logs", response_model=List[AuditLogResponse])
def list_audit_logs(
    limit: int = Query(50, ge=1, le=200),
    org: Organization = Depends(get_current_organization),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.STAFF)),
    db: Session = Depends(get_db),
):
    """Retrieve immutable cryptographically chained audit log entries."""
    service = AuditService(db)
    return service.list_logs(org.id, limit=limit)


@audit_router.get("/verify", response_model=AuditChainVerificationResult)
def verify_audit_chain(
    org: Organization = Depends(get_current_organization),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    """
    Perform a complete cryptographic verification of the SHA-256 audit hash-chain.
    Detects any manual SQL edits, row deletions, or storage tampering.
    """
    service = AuditService(db)
    return service.verify_chain(org.id)
