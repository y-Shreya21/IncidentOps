"""
Mitigation Agent Module.
Evaluates investigative evidence posted to the Blackboard, checks recovery runbooks,
validates preconditions, and posts mitigation proposals.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from semantic_kernel import Kernel

from core.incident_board import IncidentBoard
from core.schemas import MitigationProposal
from tools.mitigation_tools import MitigationTools

logger = logging.getLogger("ai_incidentops.mitigation_agent")


class MitigationAgent:
    """Agent that proposes mitigation strategies based on Blackboard evidence."""

    def __init__(self, board: IncidentBoard, kernel: Optional[Kernel] = None):
        self.board = board
        self.kernel = kernel or Kernel()
        self.plugin = MitigationTools()
        self.kernel.add_plugin(self.plugin, plugin_name="MitigationTools")

    async def propose_mitigation(self, incident_id: str) -> Optional[MitigationProposal]:
        """
        Reads evidence from board, matches runbooks, validates preconditions,
        and posts structured mitigation proposal.
        """
        incident = self.board.get_incident(incident_id)
        if not incident:
            logger.error(f"[Mitigation Agent] Incident {incident_id} not found on Blackboard")
            return None

        logger.info(f"[Mitigation Agent] Evaluating mitigation options for incident {incident_id}")

        evidence_list = incident.evidence
        log_evidence = [e for e in evidence_list if e.agent == "Logs Agent"]
        dep_evidence = [e for e in evidence_list if e.agent == "Dependency Agent"]

        # Summarize evidence
        has_log_errors = any(e.raw_data.get("has_errors", False) or e.raw_data.get("pattern_type") for e in log_evidence)
        primary_pattern = ""
        for e in log_evidence:
            pat = e.raw_data.get("pattern_type")
            if pat:
                primary_pattern = pat
                break

        unhealthy_deps: List[str] = []
        for e in dep_evidence:
            if e.raw_data.get("status") == "unhealthy":
                unhealthy_deps.append(e.service)

        supporting_evidence_ids = [e.evidence_id for e in evidence_list]

        evidence_summary = {
            "has_log_errors": has_log_errors,
            "primary_pattern": primary_pattern,
            "unhealthy_dependencies": unhealthy_deps,
            "recent_deployment": ("deployment" in primary_pattern) or ("release" in incident.description.lower())
        }

        # Step 1: Determine query keyword for runbook
        query_key = primary_pattern or incident.symptom
        if not has_log_errors and not unhealthy_deps:
            query_key = "insufficient"

        # Step 2: Retrieve runbook
        rb_res = await self.kernel.invoke(
            plugin_name="MitigationTools",
            function_name="retrieve_runbook",
            incident_type=query_key
        )
        rb_info = rb_res.value
        runbook = rb_info.get("runbook") or {}

        recommended_action = runbook.get("recommended_action", "hold_and_escalate")
        target_service = runbook.get("target_service", incident.service)
        if target_service == "affected_service":
            target_service = incident.service
        elif target_service == "postgres" and "postgres" in unhealthy_deps:
            target_service = "postgres"

        # Step 3: Evaluate preconditions
        pre_res = await self.kernel.invoke(
            plugin_name="MitigationTools",
            function_name="evaluate_mitigation_preconditions",
            action=recommended_action,
            target_service=target_service,
            evidence_summary=evidence_summary
        )
        precond = pre_res.value

        action = precond["action"]
        risk_level = precond["risk_level"]
        reason = precond["reason"]

        proposal_id = f"PROP-{incident_id[-3:] if len(incident_id) >= 3 else '001'}-001"
        proposal = MitigationProposal(
            proposal_id=proposal_id,
            agent="Mitigation Agent",
            proposed_action=action,
            target_service=target_service,
            reason=reason,
            supporting_evidence=supporting_evidence_ids,
            risk_level=risk_level
        )

        self.board.post_mitigation_proposal(incident_id, proposal)
        logger.info(f"[Mitigation Agent] Posted proposal {proposal_id}: {action} on {target_service}")
        return proposal
