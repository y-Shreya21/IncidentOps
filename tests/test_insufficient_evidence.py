"""
Automated Test for Scenario D: Insufficient Evidence Handling.
Verifies that the system safely halts, avoids inventing root causes,
and escalates when logs and dependency checks show no clear failure.
"""

import pytest
from pathlib import Path
from core.incident_board import IncidentBoard
from core.orchestrator import IncidentOrchestrator
from core.schemas import IncidentStatus
from infrastructure.simulation_runner import SimulationRunner


@pytest.mark.asyncio
async def test_scenario_d_insufficient_evidence(tmp_path: Path):
    db_file = tmp_path / "test_incidentops.db"
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    sim = SimulationRunner(logs_dir=logs_dir)
    alert_payload = sim.setup_insufficient_evidence()

    board = IncidentBoard(db_file)
    orchestrator = IncidentOrchestrator(board, logs_dir=logs_dir)

    # Execute war-room cycle
    postmortem = await orchestrator.run_incident_response(alert_payload)

    # 1. Verify Incident State
    incident = board.get_incident(postmortem.incident_id)
    assert incident is not None

    # 2. Verify Logs Agent found no errors
    log_evidence = [e for e in incident.evidence if e.agent == "Logs Agent"]
    assert len(log_evidence) > 0
    assert not log_evidence[0].raw_data.get("has_errors", False)

    # 3. Verify Dependencies are all healthy
    dep_evidence = [e for e in incident.evidence if e.agent == "Dependency Agent"]
    assert all(e.raw_data.get("status") == "healthy" for e in dep_evidence)

    # 4. Verify Commander Decision
    decision = incident.decision
    assert decision is not None
    assert decision.decision_status == "insufficient_evidence"
    assert decision.escalation_required is True
    assert decision.incident_status == IncidentStatus.ESCALATED
    assert decision.mitigation_decision == "hold_and_escalate"
    assert decision.confidence < 0.50
    assert "insufficient" in decision.likely_root_cause.lower()

    # 5. Verify no destructive mitigation was proposed or executed
    assert decision.mitigation_decision not in ("restart", "rollback", "failover")
