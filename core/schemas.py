"""
Data schemas and models for AI IncidentOps.
Defines strongly typed Pydantic models for the Blackboard Architecture.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class IncidentSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class IncidentStatus(str, Enum):
    INVESTIGATING = "investigating"
    MITIGATING = "mitigating"
    MITIGATED = "mitigated"
    ESCALATED = "escalated"
    RESOLVED = "resolved"


class ServiceMetadata(BaseModel):
    name: str
    tier: str = "tier-1"
    owner: str = "platform-engineering"
    health_endpoint: str = "/health"
    metrics_endpoint: str = "/metrics"
    logs_path: str = "logs/service.log"
    dependencies: List[str] = Field(default_factory=list)


class AlertPayload(BaseModel):
    service: str
    symptom: str
    severity: IncidentSeverity = IncidentSeverity.HIGH
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    description: str = ""
    incident_id: Optional[str] = None


class EvidenceItem(BaseModel):
    evidence_id: str
    agent: str
    finding: str
    service: str
    evidence_source: str
    evidence_timestamp: str
    raw_data: Dict[str, Any] = Field(default_factory=dict)


class MitigationProposal(BaseModel):
    proposal_id: str
    agent: str
    proposed_action: str  # restart, rollback, failover, hold_and_escalate
    target_service: str
    reason: str
    supporting_evidence: List[str] = Field(default_factory=list)
    risk_level: str = "low"  # low, medium, high


class CommanderDecision(BaseModel):
    incident_id: str
    likely_root_cause: str
    root_cause_evidence: List[str] = Field(default_factory=list)
    mitigation_decision: str
    target_service: str
    decision_reason: str
    decision_status: str  # recommended, escalated, insufficient_evidence
    incident_status: IncidentStatus
    confidence: float
    escalation_required: bool = False
    timestamp: Optional[str] = None


class TimelineEvent(BaseModel):
    event_id: str
    incident_id: str
    agent: str
    event_type: str
    timestamp: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    evidence_ids: List[str] = Field(default_factory=list)


class StatusUpdate(BaseModel):
    update_id: str
    incident_id: str
    severity: IncidentSeverity
    status: IncidentStatus
    timestamp: str
    headline: str
    message: str
    audience: str = "public"


class IncidentState(BaseModel):
    incident_id: str
    service: str
    symptom: str
    severity: IncidentSeverity
    status: IncidentStatus = IncidentStatus.INVESTIGATING
    created_at: str
    description: str
    evidence: List[EvidenceItem] = Field(default_factory=list)
    mitigation_proposals: List[MitigationProposal] = Field(default_factory=list)
    decision: Optional[CommanderDecision] = None
    status_updates: List[StatusUpdate] = Field(default_factory=list)
    timeline: List[TimelineEvent] = Field(default_factory=list)
    escalation_status: str = "none"


class PostmortemReport(BaseModel):
    incident_id: str
    affected_service: str
    severity: IncidentSeverity
    incident_description: str
    likely_root_cause: str
    root_cause_evidence: List[str] = Field(default_factory=list)
    logs_findings: List[str] = Field(default_factory=list)
    dependency_findings: List[str] = Field(default_factory=list)
    mitigation_recommendation: Optional[str] = None
    commander_decision: str
    decision_justification: str
    timeline: List[TimelineEvent] = Field(default_factory=list)
    escalation_status: str
    final_incident_status: IncidentStatus
    status_page_message: Optional[str] = None
    generated_at: str
