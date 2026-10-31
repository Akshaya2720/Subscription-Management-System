"""Repository layer for SLA Contracts and Tamper-Evident SHA-256 Audit Trail."""

import uuid
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session

from app.models.verification import VerificationContract, AuditLog, VerificationStatus


class VerificationRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, org_id: uuid.UUID, contract_id: uuid.UUID) -> Optional[VerificationContract]:
        return (
            self.db.query(VerificationContract)
            .filter(
                VerificationContract.organization_id == org_id,
                VerificationContract.id == contract_id,
            )
            .first()
        )

    def get_by_number(self, org_id: uuid.UUID, contract_number: str) -> Optional[VerificationContract]:
        return (
            self.db.query(VerificationContract)
            .filter(
                VerificationContract.organization_id == org_id,
                VerificationContract.contract_number == contract_number,
            )
            .first()
        )

    def list(self, org_id: uuid.UUID) -> List[VerificationContract]:
        return (
            self.db.query(VerificationContract)
            .filter(VerificationContract.organization_id == org_id)
            .order_by(VerificationContract.created_at.desc())
            .all()
        )

    def save(self, contract: VerificationContract) -> VerificationContract:
        self.db.add(contract)
        self.db.commit()
        self.db.refresh(contract)
        return contract


class AuditRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_latest_log(self, org_id: uuid.UUID) -> Optional[AuditLog]:
        return (
            self.db.query(AuditLog)
            .filter(AuditLog.organization_id == org_id)
            .order_by(AuditLog.sequence_number.desc())
            .first()
        )

    def list_logs(self, org_id: uuid.UUID, limit: int = 50) -> List[AuditLog]:
        return (
            self.db.query(AuditLog)
            .filter(AuditLog.organization_id == org_id)
            .order_by(AuditLog.sequence_number.desc())
            .limit(limit)
            .all()
        )

    def get_all_ordered(self, org_id: uuid.UUID) -> List[AuditLog]:
        return (
            self.db.query(AuditLog)
            .filter(AuditLog.organization_id == org_id)
            .order_by(AuditLog.sequence_number.asc())
            .all()
        )

    def append(self, log_entry: AuditLog) -> AuditLog:
        self.db.add(log_entry)
        self.db.commit()
        self.db.refresh(log_entry)
        return log_entry
