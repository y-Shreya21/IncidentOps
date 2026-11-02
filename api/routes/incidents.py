"""
Incident Management API Endpoints for AI IncidentOps.
Implements the Layer 4 API contract with RBAC protection and Blackboard interaction.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from core.config import settings
from core.incident_board import IncidentBoard
from core.orchestrator import IncidentOrchestrator
from core.schemas import (
    AlertPayload,
    IncidentState,
    IncidentStatus,
    PostmortemReport,
    TimelineEvent,
)
from security.auth import (
    ROLE_ADMIN,
    ROLE_RESPONDER,
    ROLE_SRE,
    ROLE_STAKEHOLDER,
    UserAuth,
    get_current_user,
    require_roles,
)

logger = logging.getLogger("ai_incidentops.api.incidents")

router = APIRouter(prefix="/incidents", tags=["Incidents"])

# Initialize board and orchestrator
board = IncidentBoard(settings.DB_PATH)
orchestrator = IncidentOrchestrator(board)


class ApproveMitigationRequest(BaseModel):
    action: str
    target_service: str
    confirmed_by_operator: bool = True
    notes: Optional[str] = "Approved after operator verification."


@router.post("", response_model=IncidentState, status_code=status.HTTP_201_CREATED)
async def create_incident(
    alert: AlertPayload,
    current_user: UserAuth = Depends(require_roles([ROLE_ADMIN, ROLE_RESPONDER, ROLE_SRE])),
):
    """Creates a new incident on the Blackboard."""
    try:
        incident_state = await orchestrator.alert_agent.process_alert(alert.model_dump())
        return incident_state
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Failed to create incident")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=List[IncidentState])
def list_incidents(
    current_user: UserAuth = Depends(get_current_user),
):
    """Retrieves all incident records on the Blackboard."""
    return board.list_incidents()


@router.get("/{incident_id}", response_model=IncidentState)
def get_incident(
    incident_id: str,
    current_user: UserAuth = Depends(get_current_user),
):
    """Retrieves complete state for a specific incident."""
    inc = board.get_incident(incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail=f"Incident '{incident_id}' not found")
    return inc


@router.post("/{incident_id}/investigate", response_model=PostmortemReport)
async def start_investigation(
    incident_id: str,
    current_user: UserAuth = Depends(require_roles([ROLE_ADMIN, ROLE_RESPONDER, ROLE_SRE])),
):
    """Triggers the full multi-agent war-room cycle for an existing incident."""
    inc = board.get_incident(incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail=f"Incident '{incident_id}' not found")

    payload = {
        "service": inc.service,
        "symptom": inc.symptom,
        "severity": inc.severity.value,
        "timestamp": inc.created_at,
        "description": inc.description,
        "incident_id": inc.incident_id,
    }
    return await orchestrator.run_incident_response(payload)


@router.get("/{incident_id}/agents")
def get_agent_activities(
    incident_id: str,
    current_user: UserAuth = Depends(get_current_user),
):
    """Retrieves agent execution records and posted evidence."""
    inc = board.get_incident(incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail=f"Incident '{incident_id}' not found")

    return {
        "incident_id": incident_id,
        "service": inc.service,
        "status": inc.status,
        "agents": {
            "alert_agent": {"status": "completed", "tools": ["validate_alert", "lookup_service_metadata"]},
            "logs_agent": {
                "status": "completed",
                "tools": ["retrieve_recent_logs", "analyze_log_patterns"],
                "evidence_count": len([e for e in inc.evidence if e.agent == "Logs Agent"]),
            },
            "dependency_agent": {
                "status": "completed",
                "tools": ["retrieve_service_dependencies", "check_service_health"],
                "evidence_count": len([e for e in inc.evidence if e.agent == "Dependency Agent"]),
            },
            "mitigation_agent": {
                "status": "completed" if inc.mitigation_proposals else "pending",
                "tools": ["retrieve_runbook", "evaluate_mitigation_preconditions"],
                "proposals_count": len(inc.mitigation_proposals),
            },
            "incident_commander": {
                "status": "completed" if inc.decision else "pending",
                "tools": ["validate_evidence", "record_incident_decision"],
                "has_decision": inc.decision is not None,
            },
            "communication_agent": {
                "status": "completed" if inc.status_updates else "pending",
                "tools": ["retrieve_status_template", "generate_status_update"],
                "updates_count": len(inc.status_updates),
            },
        },
    }


@router.get("/{incident_id}/blackboard", response_model=IncidentState)
def get_blackboard_state(
    incident_id: str,
    current_user: UserAuth = Depends(get_current_user),
):
    """Retrieves shared Blackboard state."""
    inc = board.get_incident(incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail=f"Incident '{incident_id}' not found")
    return inc


@router.get("/{incident_id}/timeline", response_model=List[TimelineEvent])
def get_timeline(
    incident_id: str,
    current_user: UserAuth = Depends(get_current_user),
):
    """Retrieves chronological append-only timeline."""
    events = board.get_timeline(incident_id)
    return events


@router.get("/{incident_id}/report", response_model=PostmortemReport)
def get_report(
    incident_id: str,
    current_user: UserAuth = Depends(get_current_user),
):
    """Retrieves postmortem report."""
    postmortem = board.generate_postmortem(incident_id)
    if not postmortem:
        raise HTTPException(status_code=404, detail=f"Postmortem for '{incident_id}' not found")
    return postmortem


@router.post("/{incident_id}/approve")
def approve_mitigation(
    incident_id: str,
    approval: ApproveMitigationRequest,
    current_user: UserAuth = Depends(require_roles([ROLE_ADMIN, ROLE_RESPONDER])),
):
    """Approves a restricted mitigation action (human safety gate)."""
    inc = board.get_incident(incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail=f"Incident '{incident_id}' not found")

    event = board.event_logger.log_event(
        incident_id=incident_id,
        agent=f"Human Operator ({current_user.username})",
        event_type="mitigation_approved",
        payload={
            "action": approval.action,
            "target_service": approval.target_service,
            "operator_role": current_user.role,
            "notes": approval.notes,
        },
    )

    board.update_status(incident_id, IncidentStatus.MITIGATED)

    return {
        "status": "approved",
        "incident_id": incident_id,
        "action": approval.action,
        "target_service": approval.target_service,
        "approved_by": current_user.username,
        "event_id": event.event_id,
    }
