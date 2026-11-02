"""
Communication Agent Module (Group-of-Three Extension).
Generates public and internal stakeholder status-page communications
strictly grounded in confirmed Blackboard incident facts.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional
from datetime import datetime, timezone
from semantic_kernel import Kernel

from core.incident_board import IncidentBoard
from core.schemas import StatusUpdate
from tools.communication_tools import CommunicationTools

logger = logging.getLogger("ai_incidentops.communication_agent")


class CommunicationAgent:
    """Agent generating stakeholder status-page updates."""

    def __init__(self, board: IncidentBoard, kernel: Optional[Kernel] = None):
        self.board = board
        self.kernel = kernel or Kernel()
        self.plugin = CommunicationTools()
        self.kernel.add_plugin(self.plugin, plugin_name="CommunicationTools")

    async def broadcast_status(self, incident_id: str) -> Optional[StatusUpdate]:
        """
        Reads confirmed state from board, generates status update, and commits to board.
        """
        incident = self.board.get_incident(incident_id)
        if not incident:
            logger.error(f"[Communication Agent] Incident {incident_id} not found on Blackboard")
            return None

        logger.info(f"[Communication Agent] Preparing status broadcast for {incident_id}")

        action = "investigation"
        if incident.decision:
            action = incident.decision.mitigation_decision
        elif incident.mitigation_proposals:
            action = incident.mitigation_proposals[0].proposed_action

        # Generate update via Semantic Kernel tool
        up_res = await self.kernel.invoke(
            plugin_name="CommunicationTools",
            function_name="generate_status_update",
            incident_id=incident_id,
            service_name=incident.service,
            symptom=incident.symptom,
            severity=incident.severity.value,
            status=incident.status.value,
            action=action
        )
        update_dict = up_res.value.get("status_update")
        if not update_dict:
            return None

        update = StatusUpdate(**update_dict)
        self.board.post_status_update(incident_id, update)
        logger.info(f"[Communication Agent] Broadcasted update {update.update_id}: '{update.headline}'")
        return update
