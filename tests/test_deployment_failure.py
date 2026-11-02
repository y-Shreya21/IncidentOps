"""
Automated Test for Scenario B: Failed Deployment.
Verifies multi-agent diagnosis and rollback recommendation on bad software releases.
"""

import pytest
from pathlib import Path
from core.incident_board import IncidentBoard
from core.orchestrator import IncidentOrchestrator
from core.schemas import IncidentSeverity
from infrastructure.simulation_runner import SimulationRunner


@pytest.mark.asyncio
async def test_scenario_b_deployment_failure(tmp_path: Path):
    db_file = tmp_path / "test_incidentops.db"
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    sim = SimulationRunner(logs_dir=logs_dir)
    alert_payload = sim.setup_deployment_failure()

    board = IncidentBoard(db_file)
    orchestrator = IncidentOrchestrator(board, logs_dir=logs_dir)

    # Execute war-room cycle
    postmortem = await orchestrator.run_incident_response(alert_payload)

    # 1. Verify Incident State
    incident = board.get_incident(postmortem.incident_id)
    assert incident is not None
    assert incident.service == "payment-api"

    # 2. Verify Logs Agent identified deployment error
    log_evidence = [e for e in incident.evidence if e.agent == "Logs Agent"]
    assert len(log_evidence) > 0
    assert any("deployment" in e.finding.lower() for e in log_evidence)

    # 3. Verify Dependencies are healthy
    dep_evidence = [e for e in incident.evidence if e.agent == "Dependency Agent"]
    assert len(dep_evidence) > 0
    postgres_dep = [e for e in dep_evidence if e.service == "postgres"]
    assert len(postgres_dep) > 0
    assert postgres_dep[0].raw_data.get("status") == "healthy"

    # 4. Verify Mitigation Proposal is Rollback
    assert len(incident.mitigation_proposals) > 0
    proposal = incident.mitigation_proposals[0]
    assert proposal.proposed_action == "rollback"
    assert proposal.target_service == "payment-api"

    # 5. Verify Commander Decision
    decision = incident.decision
    assert decision is not None
    assert "deployment" in decision.likely_root_cause.lower() or "regression" in decision.likely_root_cause.lower()
    assert decision.mitigation_decision == "rollback"
    assert decision.confidence >= 0.85
    assert not decision.escalation_required

    # 6. Verify Evidence References
    board_evidence_ids = {e.evidence_id for e in incident.evidence}
    for cited_id in decision.root_cause_evidence:
        assert cited_id in board_evidence_ids
