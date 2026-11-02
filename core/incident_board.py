"""
Shared Incident Board for AI IncidentOps.
Implements the Blackboard Architecture: central repository of incident state,
evidence registry, mitigation proposals, decisions, and event logs.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.event_logger import EventLogger
from core.schemas import (
    CommanderDecision,
    EvidenceItem,
    IncidentSeverity,
    IncidentState,
    IncidentStatus,
    MitigationProposal,
    PostmortemReport,
    StatusUpdate,
    TimelineEvent,
)


class IncidentBoard:
    """Central Blackboard interface accessed by all agents."""

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self.event_logger = EventLogger(self.db_path)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._lock:
            with self._get_connection() as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS incidents (
                        incident_id TEXT PRIMARY KEY,
                        service TEXT NOT NULL,
                        symptom TEXT NOT NULL,
                        severity TEXT NOT NULL,
                        status TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        description TEXT NOT NULL,
                        escalation_status TEXT DEFAULT 'none'
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS evidence (
                        evidence_id TEXT NOT NULL,
                        incident_id TEXT NOT NULL,
                        agent TEXT NOT NULL,
                        finding TEXT NOT NULL,
                        service TEXT NOT NULL,
                        evidence_source TEXT NOT NULL,
                        evidence_timestamp TEXT NOT NULL,
                        raw_data TEXT NOT NULL,
                        PRIMARY KEY (incident_id, evidence_id)
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS mitigation_proposals (
                        proposal_id TEXT NOT NULL,
                        incident_id TEXT NOT NULL,
                        agent TEXT NOT NULL,
                        proposed_action TEXT NOT NULL,
                        target_service TEXT NOT NULL,
                        reason TEXT NOT NULL,
                        supporting_evidence TEXT NOT NULL,
                        risk_level TEXT NOT NULL,
                        PRIMARY KEY (incident_id, proposal_id)
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS decisions (
                        incident_id TEXT PRIMARY KEY,
                        likely_root_cause TEXT NOT NULL,
                        root_cause_evidence TEXT NOT NULL,
                        mitigation_decision TEXT NOT NULL,
                        target_service TEXT NOT NULL,
                        decision_reason TEXT NOT NULL,
                        decision_status TEXT NOT NULL,
                        incident_status TEXT NOT NULL,
                        confidence REAL NOT NULL,
                        escalation_required INTEGER NOT NULL,
                        timestamp TEXT NOT NULL
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS status_updates (
                        update_id TEXT NOT NULL,
                        incident_id TEXT NOT NULL,
                        severity TEXT NOT NULL,
                        status TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        headline TEXT NOT NULL,
                        message TEXT NOT NULL,
                        audience TEXT NOT NULL,
                        PRIMARY KEY (incident_id, update_id)
                    )
                """)
                conn.commit()

    def create_incident(
        self,
        service: str,
        symptom: str,
        severity: IncidentSeverity = IncidentSeverity.HIGH,
        description: str = "",
        timestamp: Optional[str] = None,
        incident_id: Optional[str] = None
    ) -> IncidentState:
        """Initializes a new incident on the Blackboard."""
        if not timestamp:
            timestamp = datetime.now(timezone.utc).isoformat()
        
        with self._lock:
            with self._get_connection() as conn:
                if not incident_id:
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM incidents")
                    count = cursor.fetchone()[0] + 1
                    incident_id = f"INC-{count:03d}"

                conn.execute(
                    """
                    INSERT INTO incidents (incident_id, service, symptom, severity, status, created_at, description, escalation_status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        incident_id,
                        service,
                        symptom,
                        severity.value if isinstance(severity, IncidentSeverity) else str(severity),
                        IncidentStatus.INVESTIGATING.value,
                        timestamp,
                        description,
                        "none"
                    )
                )
                conn.commit()

        # Log creation event
        self.event_logger.log_event(
            incident_id=incident_id,
            agent="Alert Agent",
            event_type="incident_created",
            payload={
                "service": service,
                "symptom": symptom,
                "severity": severity.value if isinstance(severity, IncidentSeverity) else str(severity),
                "description": description
            },
            timestamp=timestamp
        )

        return self.get_incident(incident_id)

    def get_incident(self, incident_id: str) -> Optional[IncidentState]:
        """Reads complete current state from the Blackboard."""
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT incident_id, service, symptom, severity, status, created_at, description, escalation_status FROM incidents WHERE incident_id = ?",
                    (incident_id,)
                )
                inc_row = cursor.fetchone()
                if not inc_row:
                    return None

                # Evidence
                cursor.execute(
                    "SELECT evidence_id, agent, finding, service, evidence_source, evidence_timestamp, raw_data FROM evidence WHERE incident_id = ? ORDER BY evidence_id ASC",
                    (incident_id,)
                )
                evidence_rows = cursor.fetchall()
                evidence_list = [
                    EvidenceItem(
                        evidence_id=r["evidence_id"],
                        agent=r["agent"],
                        finding=r["finding"],
                        service=r["service"],
                        evidence_source=r["evidence_source"],
                        evidence_timestamp=r["evidence_timestamp"],
                        raw_data=json.loads(r["raw_data"])
                    )
                    for r in evidence_rows
                ]

                # Mitigation Proposals
                cursor.execute(
                    "SELECT proposal_id, agent, proposed_action, target_service, reason, supporting_evidence, risk_level FROM mitigation_proposals WHERE incident_id = ? ORDER BY proposal_id ASC",
                    (incident_id,)
                )
                prop_rows = cursor.fetchall()
                proposals = [
                    MitigationProposal(
                        proposal_id=r["proposal_id"],
                        agent=r["agent"],
                        proposed_action=r["proposed_action"],
                        target_service=r["target_service"],
                        reason=r["reason"],
                        supporting_evidence=json.loads(r["supporting_evidence"]),
                        risk_level=r["risk_level"]
                    )
                    for r in prop_rows
                ]

                # Decision
                cursor.execute(
                    "SELECT likely_root_cause, root_cause_evidence, mitigation_decision, target_service, decision_reason, decision_status, incident_status, confidence, escalation_required, timestamp FROM decisions WHERE incident_id = ?",
                    (incident_id,)
                )
                dec_row = cursor.fetchone()
                decision = None
                if dec_row:
                    decision = CommanderDecision(
                        incident_id=incident_id,
                        likely_root_cause=dec_row["likely_root_cause"],
                        root_cause_evidence=json.loads(dec_row["root_cause_evidence"]),
                        mitigation_decision=dec_row["mitigation_decision"],
                        target_service=dec_row["target_service"],
                        decision_reason=dec_row["decision_reason"],
                        decision_status=dec_row["decision_status"],
                        incident_status=IncidentStatus(dec_row["incident_status"]),
                        confidence=dec_row["confidence"],
                        escalation_required=bool(dec_row["escalation_required"]),
                        timestamp=dec_row["timestamp"]
                    )

                # Status updates
                cursor.execute(
                    "SELECT update_id, severity, status, timestamp, headline, message, audience FROM status_updates WHERE incident_id = ? ORDER BY timestamp ASC",
                    (incident_id,)
                )
                up_rows = cursor.fetchall()
                status_updates = [
                    StatusUpdate(
                        update_id=r["update_id"],
                        incident_id=incident_id,
                        severity=IncidentSeverity(r["severity"]),
                        status=IncidentStatus(r["status"]),
                        timestamp=r["timestamp"],
                        headline=r["headline"],
                        message=r["message"],
                        audience=r["audience"]
                    )
                    for r in up_rows
                ]

        timeline = self.event_logger.get_events(incident_id)

        return IncidentState(
            incident_id=inc_row["incident_id"],
            service=inc_row["service"],
            symptom=inc_row["symptom"],
            severity=IncidentSeverity(inc_row["severity"]),
            status=IncidentStatus(inc_row["status"]),
            created_at=inc_row["created_at"],
            description=inc_row["description"],
            evidence=evidence_list,
            mitigation_proposals=proposals,
            decision=decision,
            status_updates=status_updates,
            timeline=timeline,
            escalation_status=inc_row["escalation_status"]
        )

    def list_incidents(self) -> List[IncidentState]:
        """Lists all incidents stored in the Blackboard."""
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT incident_id FROM incidents ORDER BY created_at DESC")
                rows = cursor.fetchall()
        
        return [self.get_incident(r["incident_id"]) for r in rows if r]

    def post_evidence(self, incident_id: str, evidence: EvidenceItem) -> TimelineEvent:
        """Posts an evidence finding to the Blackboard."""
        with self._lock:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO evidence (evidence_id, incident_id, agent, finding, service, evidence_source, evidence_timestamp, raw_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        evidence.evidence_id,
                        incident_id,
                        evidence.agent,
                        evidence.finding,
                        evidence.service,
                        evidence.evidence_source,
                        evidence.evidence_timestamp,
                        json.dumps(evidence.raw_data)
                    )
                )
                conn.commit()

        # Log event in append-only log
        return self.event_logger.log_event(
            incident_id=incident_id,
            agent=evidence.agent,
            event_type="evidence_posted",
            payload={
                "evidence_id": evidence.evidence_id,
                "finding": evidence.finding,
                "service": evidence.service,
                "source": evidence.evidence_source
            },
            evidence_ids=[evidence.evidence_id],
            timestamp=evidence.evidence_timestamp
        )

    def post_mitigation_proposal(self, incident_id: str, proposal: MitigationProposal) -> TimelineEvent:
        """Posts a mitigation recommendation to the Blackboard."""
        with self._lock:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO mitigation_proposals (proposal_id, incident_id, agent, proposed_action, target_service, reason, supporting_evidence, risk_level)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        proposal.proposal_id,
                        incident_id,
                        proposal.agent,
                        proposal.proposed_action,
                        proposal.target_service,
                        proposal.reason,
                        json.dumps(proposal.supporting_evidence),
                        proposal.risk_level
                    )
                )
                conn.commit()

        return self.event_logger.log_event(
            incident_id=incident_id,
            agent=proposal.agent,
            event_type="mitigation_proposed",
            payload={
                "proposal_id": proposal.proposal_id,
                "proposed_action": proposal.proposed_action,
                "target_service": proposal.target_service,
                "reason": proposal.reason,
                "risk_level": proposal.risk_level
            },
            evidence_ids=proposal.supporting_evidence
        )

    def record_decision(self, incident_id: str, decision: CommanderDecision) -> TimelineEvent:
        """Records the Incident Commander's final decision on the Blackboard."""
        now = decision.timestamp or datetime.now(timezone.utc).isoformat()
        decision.timestamp = now

        with self._lock:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO decisions (
                        incident_id, likely_root_cause, root_cause_evidence, mitigation_decision,
                        target_service, decision_reason, decision_status, incident_status,
                        confidence, escalation_required, timestamp
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        incident_id,
                        decision.likely_root_cause,
                        json.dumps(decision.root_cause_evidence),
                        decision.mitigation_decision,
                        decision.target_service,
                        decision.decision_reason,
                        decision.decision_status,
                        decision.incident_status.value,
                        decision.confidence,
                        1 if decision.escalation_required else 0,
                        now
                    )
                )
                
                # Update incident table status
                escalation = "escalated" if decision.escalation_required else "none"
                conn.execute(
                    "UPDATE incidents SET status = ?, escalation_status = ? WHERE incident_id = ?",
                    (decision.incident_status.value, escalation, incident_id)
                )
                conn.commit()

        return self.event_logger.log_event(
            incident_id=incident_id,
            agent="Incident Commander",
            event_type="decision_recorded",
            payload={
                "likely_root_cause": decision.likely_root_cause,
                "mitigation_decision": decision.mitigation_decision,
                "confidence": decision.confidence,
                "decision_status": decision.decision_status,
                "incident_status": decision.incident_status.value,
                "escalation_required": decision.escalation_required,
                "reason": decision.decision_reason
            },
            evidence_ids=decision.root_cause_evidence,
            timestamp=now
        )

    def post_status_update(self, incident_id: str, update: StatusUpdate) -> TimelineEvent:
        """Posts a public or internal status update to the Blackboard."""
        with self._lock:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO status_updates (update_id, incident_id, severity, status, timestamp, headline, message, audience)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        update.update_id,
                        incident_id,
                        update.severity.value,
                        update.status.value,
                        update.timestamp,
                        update.headline,
                        update.message,
                        update.audience
                    )
                )
                conn.commit()

        return self.event_logger.log_event(
            incident_id=incident_id,
            agent="Communication Agent",
            event_type="status_update_posted",
            payload={
                "update_id": update.update_id,
                "headline": update.headline,
                "message": update.message,
                "status": update.status.value
            },
            timestamp=update.timestamp
        )

    def update_status(self, incident_id: str, status: IncidentStatus) -> TimelineEvent:
        """Updates the incident status."""
        with self._lock:
            with self._get_connection() as conn:
                conn.execute(
                    "UPDATE incidents SET status = ? WHERE incident_id = ?",
                    (status.value, incident_id)
                )
                conn.commit()

        return self.event_logger.log_event(
            incident_id=incident_id,
            agent="System",
            event_type="status_changed",
            payload={"status": status.value}
        )

    def get_timeline(self, incident_id: str) -> List[TimelineEvent]:
        """Returns the chronological timeline of events."""
        return self.event_logger.get_events(incident_id)

    def generate_postmortem(self, incident_id: str) -> Optional[PostmortemReport]:
        """Assembles a structured postmortem report from verified Blackboard data."""
        state = self.get_incident(incident_id)
        if not state:
            return None

        logs_findings = [
            f"[{e.evidence_id}] {e.finding} (source: {e.evidence_source})"
            for e in state.evidence
            if e.agent == "Logs Agent"
        ]
        dep_findings = [
            f"[{e.evidence_id}] {e.finding} (service: {e.service})"
            for e in state.evidence
            if e.agent == "Dependency Agent"
        ]

        rec = state.mitigation_proposals[0].proposed_action if state.mitigation_proposals else None
        
        status_msg = state.status_updates[-1].message if state.status_updates else None

        decision = state.decision or CommanderDecision(
            incident_id=incident_id,
            likely_root_cause="Under Investigation",
            root_cause_evidence=[],
            mitigation_decision="none",
            target_service=state.service,
            decision_reason="Investigation incomplete",
            decision_status="pending",
            incident_status=state.status,
            confidence=0.0
        )

        return PostmortemReport(
            incident_id=state.incident_id,
            affected_service=state.service,
            severity=state.severity,
            incident_description=state.description or state.symptom,
            likely_root_cause=decision.likely_root_cause,
            root_cause_evidence=decision.root_cause_evidence,
            logs_findings=logs_findings,
            dependency_findings=dep_findings,
            mitigation_recommendation=rec,
            commander_decision=decision.mitigation_decision,
            decision_justification=decision.decision_reason,
            timeline=state.timeline,
            escalation_status=state.escalation_status,
            final_incident_status=state.status,
            status_page_message=status_msg,
            generated_at=datetime.now(timezone.utc).isoformat()
        )
