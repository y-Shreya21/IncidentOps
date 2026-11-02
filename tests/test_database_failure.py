"""
Automated Test for Scenario A: Database Connectivity Failure.
Verifies end-to-end multi-agent incident response on an unavailable database.
"""

import pytest
from pathlib import Path
from core.incident_board import IncidentBoard
from core.orchestrator import IncidentOrchestrator
from core.schemas import IncidentSeverity, IncidentStatus
from infrastructure.simulation_runner import SimulationRunner


@pytest.mark.asyncio
async def test_scenario_a_database_failure(tmp_path: Path):
    db_file = tmp_path / "test_incidentops.db"
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    sim = SimulationRunner(logs_dir=logs_dir)
    alert_payload = sim.setup_database_failure()

    board = IncidentBoard(db_file)
    orchestrator = IncidentOrchestrator(board, logs_dir=logs_dir)

    # Execute war-room response
    postmortem = await orchestrator.run_incident_response(alert_payload)

    # 1. Verify Incident State
    incident = board.get_incident(postmortem.incident_id)
    assert incident is not None
    assert incident.service == "payment-api"
    assert incident.severity == IncidentSeverity.CRITICAL

    # 2. Verify Logs Agent Evidence
    log_evidence = [e for e in incident.evidence if e.agent == "Logs Agent"]
    assert len(log_evidence) > 0
    assert any("database" in e.finding.lower() or "connection" in e.finding.lower() for e in log_evidence)
    assert any("payment-api.log" in e.evidence_source for e in log_evidence)

    # 3. Verify Dependency Agent Evidence
    dep_evidence = [e for e in incident.evidence if e.agent == "Dependency Agent"]
    assert len(dep_evidence) > 0
    postgres_dep = [e for e in dep_evidence if e.service == "postgres"]
    assert len(postgres_dep) > 0
    assert postgres_dep[0].raw_data.get("status") == "unhealthy"

    # 4. Verify Mitigation Proposal
    assert len(incident.mitigation_proposals) > 0
    proposal = incident.mitigation_proposals[0]
    assert proposal.proposed_action == "restart"
    assert proposal.target_service == "postgres"
    assert len(proposal.supporting_evidence) > 0

    # 5. Verify Commander Decision
    decision = incident.decision
    assert decision is not None
    assert "database" in decision.likely_root_cause.lower()
    assert decision.mitigation_decision == "restart"
    assert decision.target_service == "postgres"
    assert decision.decision_status == "recommended"
    assert decision.confidence >= 0.85
    assert not decision.escalation_required

    # 6. Verify Evidence References
    assert len(decision.root_cause_evidence) > 0
    board_evidence_ids = {e.evidence_id for e in incident.evidence}
    for cited_id in decision.root_cause_evidence:
        assert cited_id in board_evidence_ids, f"Cited ID {cited_id} must exist on Blackboard"

    # 7. Verify Timeline Integrity
    timeline = board.get_timeline(incident.incident_id)
    assert len(timeline) >= 5
    agents_in_timeline = {event.agent for event in timeline}
    assert "Alert Agent" in agents_in_timeline
    assert "Logs Agent" in agents_in_timeline
    assert "Dependency Agent" in agents_in_timeline
    assert "Mitigation Agent" in agents_in_timeline
    assert "Incident Commander" in agents_in_timeline
    assert "Communication Agent" in agents_in_timeline

    # 8. Verify Communication Agent Update
    assert len(incident.status_updates) > 0
    comm = incident.status_updates[-1]
    assert comm.severity == IncidentSeverity.CRITICAL
    assert "investigating" in comm.status.value.lower() or "mitigating" in comm.status.value.lower()
    assert "payment-api" in comm.message.lower()
