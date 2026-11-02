"""
Automated Tests for Shared Incident Board & Append-Only Event Log.
Verifies SQLite persistence, concurrent posting safety, and timeline immutability.
"""

import asyncio
import pytest
from pathlib import Path
from core.incident_board import IncidentBoard
from core.schemas import EvidenceItem, IncidentSeverity, IncidentStatus


def test_board_crud_and_persistence(tmp_path: Path):
    db_file = tmp_path / "board_test.db"
    board1 = IncidentBoard(db_file)

    inc = board1.create_incident(
        service="payment-api",
        symptom="HTTP 500 errors",
        severity=IncidentSeverity.CRITICAL,
        description="Checkout failing"
    )
    inc_id = inc.incident_id

    # Post evidence
    ev = EvidenceItem(
        evidence_id="LOG-TEST-001",
        agent="Logs Agent",
        finding="Connection refused to db",
        service="payment-api",
        evidence_source="logs/payment-api.log",
        evidence_timestamp="2026-11-02T10:00:00Z",
        raw_data={"error": "OperationalError"}
    )
    board1.post_evidence(inc_id, ev)

    # Reload from fresh board instance
    board2 = IncidentBoard(db_file)
    reloaded = board2.get_incident(inc_id)
    assert reloaded is not None
    assert reloaded.service == "payment-api"
    assert reloaded.severity == IncidentSeverity.CRITICAL
    assert len(reloaded.evidence) == 1
    assert reloaded.evidence[0].evidence_id == "LOG-TEST-001"
    assert reloaded.evidence[0].finding == "Connection refused to db"

    # Verify append-only timeline
    timeline = board2.get_timeline(inc_id)
    assert len(timeline) >= 2
    assert timeline[0].event_type == "incident_created"
    assert timeline[1].event_type == "evidence_posted"


@pytest.mark.asyncio
async def test_concurrent_evidence_posting(tmp_path: Path):
    """Verifies that concurrent posts from multiple agents do not conflict or corrupt."""
    db_file = tmp_path / "concurrent_test.db"
    board = IncidentBoard(db_file)

    inc = board.create_incident(service="auth-service", symptom="Auth failure")
    inc_id = inc.incident_id

    async def post_worker(agent_name: str, index: int):
        ev = EvidenceItem(
            evidence_id=f"EV-{agent_name[:3].upper()}-{index:03d}",
            agent=agent_name,
            finding=f"Finding from {agent_name} #{index}",
            service="auth-service",
            evidence_source="telemetry",
            evidence_timestamp="2026-11-02T10:00:00Z",
            raw_data={"worker_id": index}
        )
        # Use asyncio.to_thread to simulate parallel OS threads posting to SQLite
        await asyncio.to_thread(board.post_evidence, inc_id, ev)

    # Launch 20 concurrent postings
    tasks = []
    for i in range(10):
        tasks.append(post_worker("Logs Agent", i))
        tasks.append(post_worker("Dependency Agent", i))

    await asyncio.gather(*tasks)

    # Verify all 20 evidence items were stored
    state = board.get_incident(inc_id)
    assert state is not None
    assert len(state.evidence) == 20

    # Verify append-only event log captured all 20 + 1 creation event
    timeline = board.get_timeline(inc_id)
    assert len(timeline) == 21
