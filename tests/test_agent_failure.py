"""
Automated Test for Scenario E: Agent Failure & Graceful Degradation Handling.
Verifies that when an investigative tool encounters missing files or errors,
the system logs the failure immutably, avoids crashing, and safe escalation occurs.
"""

import pytest
from pathlib import Path
from core.incident_board import IncidentBoard
from core.orchestrator import IncidentOrchestrator
from core.schemas import IncidentSeverity, IncidentStatus


@pytest.mark.asyncio
async def test_scenario_e_agent_failure_handling(tmp_path: Path):
    db_file = tmp_path / "test_incidentops.db"
    # Provide an empty logs directory with no files
    empty_logs_dir = tmp_path / "empty_logs"
    empty_logs_dir.mkdir(parents=True, exist_ok=True)

    board = IncidentBoard(db_file)
    orchestrator = IncidentOrchestrator(board, logs_dir=empty_logs_dir)

    # Ingest alert for non-existent service to test tool missing file handling
    alert_payload = {
        "service": "unknown-nonexistent-svc",
        "symptom": "Timeout reported by edge gateway",
        "severity": "high",
        "timestamp": "2026-11-02T10:00:00Z",
        "description": "Vague anomaly report on unregistered service."
    }

    # Execute war-room cycle - should not crash
    postmortem = await orchestrator.run_incident_response(alert_payload)

    # 1. Verify Incident was recorded
    incident = board.get_incident(postmortem.incident_id)
    assert incident is not None

    # 2. Verify Incident Commander handled missing evidence safely
    decision = incident.decision
    assert decision is not None
    assert decision.escalation_required is True
    assert decision.mitigation_decision == "hold_and_escalate"
    assert "insufficient" in decision.likely_root_cause.lower()

    # 3. Verify Timeline integrity
    timeline = board.get_timeline(incident.incident_id)
    assert len(timeline) >= 4
    agents_present = {e.agent for e in timeline}
    assert "Incident Commander" in agents_present
