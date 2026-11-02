"""
Automated Test for Scenario C: High CPU Utilization.
Verifies multi-agent diagnosis and worker restart recommendation when threads are saturated.
"""

import pytest
from pathlib import Path
from core.incident_board import IncidentBoard
from core.orchestrator import IncidentOrchestrator
from core.schemas import IncidentSeverity
from infrastructure.simulation_runner import SimulationRunner


@pytest.mark.asyncio
async def test_scenario_c_high_cpu(tmp_path: Path):
    db_file = tmp_path / "test_incidentops.db"
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    sim = SimulationRunner(logs_dir=logs_dir)
    alert_payload = sim.setup_high_cpu()

    board = IncidentBoard(db_file)
    orchestrator = IncidentOrchestrator(board, logs_dir=logs_dir)

    # Execute war-room cycle
    postmortem = await orchestrator.run_incident_response(alert_payload)

    # 1. Verify Incident State
    incident = board.get_incident(postmortem.incident_id)
    assert incident is not None
    assert incident.service == "payment-api"
    assert incident.severity == IncidentSeverity.HIGH

    # 2. Verify Logs Agent identified CPU exhaustion pattern
    log_evidence = [e for e in incident.evidence if e.agent == "Logs Agent"]
    assert len(log_evidence) > 0
    assert any("cpu" in e.finding.lower() or "thread" in e.finding.lower() or "saturation" in e.finding.lower() for e in log_evidence)

    # 3. Verify Mitigation Proposal is Restart
    assert len(incident.mitigation_proposals) > 0
    proposal = incident.mitigation_proposals[0]
    assert proposal.proposed_action == "restart"
    assert proposal.target_service == "payment-api"

    # 4. Verify Commander Decision
    decision = incident.decision
    assert decision is not None
    assert "cpu" in decision.likely_root_cause.lower() or "saturation" in decision.likely_root_cause.lower()
    assert decision.mitigation_decision == "restart"
    assert decision.confidence >= 0.80
    assert not decision.escalation_required

    # 5. Verify Evidence References
    board_evidence_ids = {e.evidence_id for e in incident.evidence}
    for cited_id in decision.root_cause_evidence:
        assert cited_id in board_evidence_ids
