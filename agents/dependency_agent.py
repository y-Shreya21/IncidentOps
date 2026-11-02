"""
Dependency Agent Module.
Inspects service dependency topologies, executes health checks,
and posts authentic dependency health evidence to the shared Blackboard.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from semantic_kernel import Kernel

from core.incident_board import IncidentBoard
from core.schemas import EvidenceItem
from tools.dependency_tools import DependencyTools

logger = logging.getLogger("ai_incidentops.dependency_agent")


class DependencyAgent:
    """Agent that maps dependencies and executes health checks."""

    def __init__(self, board: IncidentBoard, kernel: Optional[Kernel] = None, logs_dir: Optional[Path] = None):
        self.board = board
        self.kernel = kernel or Kernel()
        state_file = (Path(logs_dir) / "simulated_health.json") if logs_dir else None
        self.plugin = DependencyTools(state_file=state_file)
        self.kernel.add_plugin(self.plugin, plugin_name="DependencyTools")

    async def investigate(self, incident_id: str) -> List[EvidenceItem]:
        """
        Retrieves service dependencies from registry and performs health checks.
        """
        incident = self.board.get_incident(incident_id)
        if not incident:
            logger.error(f"[Dependency Agent] Incident {incident_id} not found on Blackboard")
            return []

        service_name = incident.service
        logger.info(f"[Dependency Agent] Investigating dependencies for: {service_name}")

        # Step 1: Retrieve service dependencies
        dep_res = await self.kernel.invoke(
            plugin_name="DependencyTools",
            function_name="retrieve_service_dependencies",
            service_name=service_name
        )
        dep_info = dep_res.value
        dependencies = dep_info.get("dependencies", [])

        evidence_items: List[EvidenceItem] = []
        now = datetime.now(timezone.utc).isoformat()

        # Also check the service itself
        all_targets = [service_name] + dependencies

        for idx, target_svc in enumerate(all_targets, start=1):
            # Step 2: Check health of each service
            health_res = await self.kernel.invoke(
                plugin_name="DependencyTools",
                function_name="check_service_health",
                service_name=target_svc
            )
            health = health_res.value
            status = health.get("status", "unknown")
            latency = health.get("latency_ms", 0)
            err = health.get("error")

            is_direct = (target_svc == service_name)
            role_desc = "target service" if is_direct else f"dependency of {service_name}"
            
            finding = f"Health check for {target_svc} ({role_desc}): status={status}, latency={latency:.1f}ms"
            if err:
                finding += f", error='{err}'"

            evidence_id = f"DEP-{incident_id[-3:] if len(incident_id) >= 3 else '001'}-{idx:03d}"
            item = EvidenceItem(
                evidence_id=evidence_id,
                agent="Dependency Agent",
                finding=finding,
                service=target_svc,
                evidence_source=f"health-probe://{target_svc}",
                evidence_timestamp=now,
                raw_data=health
            )
            self.board.post_evidence(incident_id, item)
            evidence_items.append(item)
            logger.info(f"[Dependency Agent] Posted evidence {evidence_id}: {target_svc} is {status}")

        return evidence_items
