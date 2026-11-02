"""
Alert Agent Module.
Responsible for validating incoming incident signals, looking up service metadata,
normalizing severity levels, and creating initial incident records on the Blackboard.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional
from datetime import datetime, timezone
from semantic_kernel import Kernel

from core.incident_board import IncidentBoard
from core.schemas import AlertPayload, IncidentSeverity, IncidentState
from tools.alert_tools import AlertTools

logger = logging.getLogger("ai_incidentops.alert_agent")


class AlertAgent:
    """Agent that ingests, validates, and registers incidents on the Blackboard."""

    def __init__(self, board: IncidentBoard, kernel: Optional[Kernel] = None):
        self.board = board
        self.kernel = kernel or Kernel()
        self.plugin = AlertTools()
        self.kernel.add_plugin(self.plugin, plugin_name="AlertTools")

    async def process_alert(self, alert_data: Dict[str, Any]) -> IncidentState:
        """
        Validates alert, enriches with service metadata, and posts to shared board.
        """
        logger.info(f"[Alert Agent] Ingesting alert: {alert_data.get('service', 'unknown')}")

        # Step 1: Validate alert using Semantic Kernel tool
        val_result = await self.kernel.invoke(
            plugin_name="AlertTools",
            function_name="validate_alert",
            alert_data=alert_data
        )
        validation = val_result.value

        if not validation["valid"]:
            raise ValueError(f"Alert validation failed: {validation['error']}")

        normalized = validation["normalized_alert"]
        service_name = normalized["service"]

        # Step 2: Lookup service metadata
        meta_result = await self.kernel.invoke(
            plugin_name="AlertTools",
            function_name="lookup_service_metadata",
            service_name=service_name
        )
        metadata_res = meta_result.value
        metadata = metadata_res.get("metadata") or {}

        # Enrich description if service tier/owner is found
        owner = metadata.get("owner", "unknown")
        tier = metadata.get("tier", "unknown")
        enhanced_description = (
            f"{normalized['description']} | Affected: {service_name} (Tier: {tier}, Owner: {owner})"
        )

        ts = normalized.get("timestamp") or datetime.now(timezone.utc).isoformat()
        sev = IncidentSeverity(normalized["severity"])

        # Step 3: Create incident on Blackboard
        incident_state = self.board.create_incident(
            service=service_name,
            symptom=normalized["symptom"],
            severity=sev,
            description=enhanced_description,
            timestamp=ts,
            incident_id=normalized.get("incident_id")
        )

        logger.info(f"[Alert Agent] Registered {incident_state.incident_id} on Blackboard")
        return incident_state
