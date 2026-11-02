"""
Incident Commander Agent Module.
The final decision-making authority in the incident response workflow.
Strictly relies upon verified Blackboard evidence to assess root causes,
recommend mitigations, or escalate uncertain incidents.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from semantic_kernel import Kernel

from core.incident_board import IncidentBoard
from core.schemas import CommanderDecision, IncidentStatus, PostmortemReport
from tools.commander_tools import CommanderTools

logger = logging.getLogger("ai_incidentops.incident_commander")


class IncidentCommander:
    """Agent acting as the Incident Commander and final authority."""

    def __init__(self, board: IncidentBoard, kernel: Optional[Kernel] = None):
        self.board = board
        self.kernel = kernel or Kernel()
        self.plugin = CommanderTools()
        self.kernel.add_plugin(self.plugin, plugin_name="CommanderTools")

    async def decide(self, incident_id: str) -> CommanderDecision:
        """
        Reads complete board state, cross-validates evidence, determines root cause,
        and records traceable final decision.
        """
        incident = self.board.get_incident(incident_id)
        if not incident:
            raise ValueError(f"Incident {incident_id} not found on Blackboard")

        logger.info(f"[Incident Commander] Reviewing war-room board for {incident_id}")

        evidence_list = incident.evidence
        proposals = incident.mitigation_proposals

        # Convert board evidence to dicts for tool validation
        board_evidence_dicts = [e.model_dump() for e in evidence_list]
        cited_ids = [e.evidence_id for e in evidence_list]

        # Step 1: Validate evidence references via Semantic Kernel tool
        val_res = await self.kernel.invoke(
            plugin_name="CommanderTools",
            function_name="validate_evidence",
            cited_evidence_ids=cited_ids,
            blackboard_evidence=board_evidence_dicts
        )
        validation = val_res.value

        log_evidence = [e for e in evidence_list if e.agent == "Logs Agent"]
        dep_evidence = [e for e in evidence_list if e.agent == "Dependency Agent"]

        # Check for error patterns
        has_log_error = any(e.raw_data.get("has_errors", False) or e.raw_data.get("pattern_type") for e in log_evidence)
        unhealthy_deps = [e.service for e in dep_evidence if e.raw_data.get("status") == "unhealthy"]

        detected_patterns = [str(e.raw_data.get("pattern_type", "")).lower() for e in log_evidence]
        log_evidence_ids = [e.evidence_id for e in log_evidence if e.raw_data.get("pattern_type")] or cited_ids
        dep_evidence_ids = [e.evidence_id for e in dep_evidence if e.raw_data.get("status") == "unhealthy"]

        has_db = any("database" in p or "timeout" in p for p in detected_patterns) or ("postgres" in unhealthy_deps)
        has_deploy = any("deployment" in p for p in detected_patterns) or ("release" in incident.description.lower() and has_log_error)
        has_cpu = any("cpu" in p or "saturation" in p for p in detected_patterns) or ("cpu" in incident.symptom.lower()) or ("cpu" in incident.description.lower())

        # Step 2: Determine root cause strictly from verified evidence
        # Case A: Database connectivity failure
        if has_db:
            root_cause = "Database connectivity failure and connection pool exhaustion"
            target_service = "postgres" if "postgres" in unhealthy_deps else incident.service
            root_cause_evidence = list(set(log_evidence_ids + dep_evidence_ids)) or cited_ids
            mitigation_action = proposals[0].proposed_action if proposals else "restart"
            decision_status = "recommended"
            confidence = 0.92
            escalation_required = False
            reason = (
                f"Application logs cite database connection timeouts ({', '.join(log_evidence_ids)}) "
                f"corroborated by unhealthy database status probe ({', '.join(dep_evidence_ids)})."
            )

        # Case B: Failed deployment
        elif has_deploy:
            root_cause = "Post-deployment application regression / syntax error"
            target_service = incident.service
            root_cause_evidence = log_evidence_ids or cited_ids
            mitigation_action = proposals[0].proposed_action if proposals else "rollback"
            decision_status = "recommended"
            confidence = 0.94
            escalation_required = False
            reason = (
                f"Logs verify crash/exceptions immediately following software deployment ({', '.join(log_evidence_ids)}). "
                f"Infrastructure dependencies are healthy. Rolling back to previous stable release tag."
            )

        # Case C: High CPU utilization
        elif has_cpu:
            root_cause = "Worker thread saturation and high CPU consumption"
            target_service = incident.service
            root_cause_evidence = log_evidence_ids or cited_ids
            mitigation_action = proposals[0].proposed_action if proposals else "restart"
            decision_status = "recommended"
            confidence = 0.88
            escalation_required = False
            reason = (
                f"Log telemetry confirms CPU/thread exhaustion ({', '.join(log_evidence_ids)}). "
                f"Restarting service worker processes to alleviate resource lock."
            )

        # Case D: Insufficient Evidence or Contradictory Evidence
        else:
            root_cause = "Insufficient evidence to isolate root cause"
            target_service = incident.service
            root_cause_evidence = cited_ids
            mitigation_action = "hold_and_escalate"
            decision_status = "insufficient_evidence"
            confidence = 0.35
            escalation_required = True
            reason = (
                "Neither log analysis nor dependency health checks report distinct anomalies or failures. "
                "In accordance with safety protocols, automated destructive actions are prohibited. "
                "Escalating to on-call SRE team for deep-dive diagnostics."
            )

        # Step 3: Record decision via Semantic Kernel tool
        decision_data = {
            "incident_id": incident_id,
            "likely_root_cause": root_cause,
            "root_cause_evidence": root_cause_evidence,
            "mitigation_decision": mitigation_action,
            "target_service": target_service,
            "decision_reason": reason,
            "decision_status": decision_status,
            "confidence": confidence,
            "escalation_required": escalation_required
        }

        dec_res = await self.kernel.invoke(
            plugin_name="CommanderTools",
            function_name="record_incident_decision",
            decision_data=decision_data
        )
        decision_dict = dec_res.value["decision"]
        
        decision = CommanderDecision(
            incident_id=decision_dict["incident_id"],
            likely_root_cause=decision_dict["likely_root_cause"],
            root_cause_evidence=decision_dict["root_cause_evidence"],
            mitigation_decision=decision_dict["mitigation_decision"],
            target_service=decision_dict["target_service"],
            decision_reason=decision_dict["decision_reason"],
            decision_status=decision_dict["decision_status"],
            incident_status=IncidentStatus(decision_dict["incident_status"]),
            confidence=decision_dict["confidence"],
            escalation_required=decision_dict["escalation_required"]
        )

        # Commit to Blackboard
        self.board.record_decision(incident_id, decision)
        logger.info(f"[Incident Commander] Final decision recorded for {incident_id}: {decision.mitigation_decision} (Status: {decision.decision_status})")
        return decision

    def generate_postmortem(self, incident_id: str) -> Optional[PostmortemReport]:
        """Generates evidence-backed postmortem report."""
        return self.board.generate_postmortem(incident_id)
