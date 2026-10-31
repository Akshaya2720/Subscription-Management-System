"""Pydantic schemas for SLA Verification and SHA-256 Audit Trail."""

import uuid
from decimal import Decimal
from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field

from app.models.verification import VerificationStatus


class VerificationContractCreate(BaseModel):
    contract_number: str = Field(..., min_length=2, max_length=50)
    subscription_id: uuid.UUID
    service_name: str = Field(..., min_length=2, max_length=255)
    sla_commitment_description: str = Field(..., min_length=2, max_length=255)
    target_uptime_percentage: Decimal = Field(default=Decimal("99.99"), ge=Decimal("0.00"), le=Decimal("100.00"))
    actual_recorded_telemetry: str = "99.99% uptime measured"
    proposed_credit_amount: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"))


class VerificationContractResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    contract_number: str
    subscription_id: uuid.UUID
    service_name: str
    sla_commitment_description: str
    target_uptime_percentage: Decimal
    actual_recorded_telemetry: str
    breach_detected: bool
    proposed_credit_amount: Decimal
    status: VerificationStatus
    adjudicated_at: Optional[datetime] = None
    adjudicated_by: Optional[uuid.UUID] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class SlaEvaluationRequest(BaseModel):
    contract_id: uuid.UUID
    measured_uptime_percentage: Decimal = Field(..., ge=Decimal("0.00"), le=Decimal("100.00"))
    telemetry_window: str = "Last 30 Days"
    invoice_id: Optional[uuid.UUID] = None


class SlaEvaluationResult(BaseModel):
    contract_id: uuid.UUID
    contract_number: str
    target_uptime_percentage: Decimal
    measured_uptime_percentage: Decimal
    breach_detected: bool
    outage_shortfall_percent: Decimal
    proposed_credit_amount: Decimal
    adjudication_status: str
    message: str


class AuditLogResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    sequence_number: int
    previous_hash: str
    current_hash: str
    entity_type: str
    entity_id: str
    action: str
    actor_email: str
    payload_json: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AuditChainVerificationResult(BaseModel):
    organization_id: uuid.UUID
    total_blocks_verified: int
    is_valid: bool
    tampered_block_sequence: Optional[int] = None
    error_detail: Optional[str] = None
    verification_timestamp: datetime
