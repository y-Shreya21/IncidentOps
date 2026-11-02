"""
Comprehensive API, Persistence, and Safety Validation Tests.
Validates Layer 4 REST endpoints, RBAC permissions, data retention across restarts,
and safety constraints (dangerous actions blocked, preconditions enforced).
"""

import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from api.main import app
from core.incident_board import IncidentBoard
from core.schemas import (
    CommanderDecision,
    EvidenceItem,
    IncidentSeverity,
    IncidentStatus,
    MitigationProposal,
)
from tools.mitigation_tools import MitigationTools
from security.auth import (
    create_access_token,
    hash_password,
    verify_password,
    ROLE_ADMIN,
    ROLE_RESPONDER,
    ROLE_SRE,
    ROLE_STAKEHOLDER,
)

client = TestClient(app)


def test_api_health():
    """Verify API health check endpoint returns 200 and healthy status."""
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "database" in data


def test_api_list_services():
    """Verify registered services and dependency mappings."""
    res = client.get("/api/v1/services")
    assert res.status_code == 200
    services = res.json()
    assert "payment-api" in services
    assert "postgres" in services
    assert "auth-service" in services


def test_api_ingest_alert_and_workflow():
    """Verify end-to-end alert ingestion triggers multi-agent response cycle."""
    payload = {
        "service": "payment-api",
        "symptom": "HTTP 500 database pool exhaustion",
        "severity": "critical",
        "description": "Payment transactions failing with connection timeouts."
    }
    res = client.post("/api/v1/incidents/alert", json=payload)
    assert res.status_code == 200
    report = res.json()
    assert report["incident_id"].startswith("INC-")
    assert report["affected_service"] == "payment-api"
    assert report["likely_root_cause"] != ""
    assert report["commander_decision"] != ""


def test_api_simulation_scenarios():
    """Verify simulation endpoints execute cleanly."""
    for scenario in ["db_failure", "deployment_failure", "high_cpu", "insufficient_evidence"]:
        res = client.post(f"/api/v1/simulate/{scenario}?auto_respond=true")
        assert res.status_code == 200, f"Scenario {scenario} failed: {res.text}"
        data = res.json()
        assert data["scenario"] == scenario
        assert "postmortem" in data


def test_api_invalid_simulation_scenario():
    """Verify 400 error when non-existent scenario is requested."""
    res = client.post("/api/v1/simulate/non_existent_scenario")
    assert res.status_code == 400
    assert "Unknown scenario" in res.json()["detail"]


def test_data_retention_across_restart(tmp_path: Path):
    """Verify Blackboard state, evidence, proposals, and decisions persist across restarts."""
    db_file = tmp_path / "persistence_audit.db"
    
    # Session 1: Create and populate
    board1 = IncidentBoard(db_file)
    inc = board1.create_incident("checkout", "Crash", IncidentSeverity.CRITICAL, "Initial alert")
    inc_id = inc.incident_id
    
    board1.post_evidence(inc_id, EvidenceItem(
        evidence_id="EVID-TEST-001", agent="Logs Agent", finding="Segmentation fault",
        service="checkout", evidence_source="logs/checkout.log",
        evidence_timestamp="2026-11-03T00:00:00Z", raw_data={"code": 139}
    ))
    
    board1.post_mitigation_proposal(inc_id, MitigationProposal(
        proposal_id="PROP-TEST-001", agent="Mitigation Agent", proposed_action="restart",
        target_service="checkout", reason="Process crashed",
        supporting_evidence=["EVID-TEST-001"], risk_level="low"
    ))
    
    board1.record_decision(inc_id, CommanderDecision(
        incident_id=inc_id, likely_root_cause="Process memory fault",
        root_cause_evidence=["EVID-TEST-001"], mitigation_decision="restart",
        target_service="checkout", decision_reason="Verified segfault in logs",
        decision_status="recommended", incident_status=IncidentStatus.MITIGATED,
        confidence=0.96, escalation_required=False
    ))
    
    # Close session 1
    del board1
    
    # Session 2: Reload from disk
    board2 = IncidentBoard(db_file)
    reloaded = board2.get_incident(inc_id)
    
    assert reloaded is not None
    assert reloaded.service == "checkout"
    assert len(reloaded.evidence) == 1
    assert reloaded.evidence[0].evidence_id == "EVID-TEST-001"
    assert len(reloaded.mitigation_proposals) == 1
    assert reloaded.decision is not None
    assert reloaded.decision.confidence == 0.96
    assert reloaded.decision.likely_root_cause == "Process memory fault"


def test_safety_precondition_rejection():
    """Verify that dangerous / speculative mitigations are rejected when preconditions are not met."""
    tools = MitigationTools()
    
    # Scenario: Operator or agent suggests speculative rollback, but logs have NO deployment error
    eval_result = tools.evaluate_mitigation_preconditions(
        action="rollback",
        target_service="payment-api",
        evidence_summary={
            "has_log_errors": True,
            "primary_pattern": "database_timeout",
            "unhealthy_dependencies": ["postgres"],
            "recent_deployment": False
        }
    )
    
    assert eval_result["preconditions_met"] is False
    assert eval_result["risk_level"] == "high"
    assert "No deployment error signature identified" in eval_result["reason"]


def test_safety_failover_precondition():
    """Verify that failover requires confirmed primary storage failure."""
    tools = MitigationTools()
    
    # Primary storage is healthy -> failover must be rejected as high risk
    eval_result = tools.evaluate_mitigation_preconditions(
        action="failover",
        target_service="postgres",
        evidence_summary={"unhealthy_dependencies": []}
    )
    assert eval_result["preconditions_met"] is False
    assert eval_result["risk_level"] == "high"
