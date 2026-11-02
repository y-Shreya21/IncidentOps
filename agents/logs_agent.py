"""
Logs Agent Module.
Investigates service and application logs, extracts error signatures,
and posts authentic log evidence to the shared Blackboard.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from semantic_kernel import Kernel

from core.incident_board import IncidentBoard
from core.schemas import EvidenceItem
from tools.log_tools import LogTools

logger = logging.getLogger("ai_incidentops.logs_agent")


class LogsAgent:
    """Agent that extracts and analyzes log evidence."""

    def __init__(self, board: IncidentBoard, kernel: Optional[Kernel] = None, logs_dir: Optional[Path] = None):
        self.board = board
        self.kernel = kernel or Kernel()
        self.plugin = LogTools(logs_dir=logs_dir)
        self.kernel.add_plugin(self.plugin, plugin_name="LogTools")

    async def investigate(self, incident_id: str) -> List[EvidenceItem]:
        """
        Reads affected service from board, gathers logs, parses patterns, and posts evidence.
        """
        incident = self.board.get_incident(incident_id)
        if not incident:
            logger.error(f"[Logs Agent] Incident {incident_id} not found on Blackboard")
            return []

        service_name = incident.service
        logger.info(f"[Logs Agent] Investigating logs for service: {service_name}")

        # Step 1: Retrieve recent logs
        log_res = await self.kernel.invoke(
            plugin_name="LogTools",
            function_name="retrieve_recent_logs",
            service_name=service_name,
            max_lines=150
        )
        logs_info = log_res.value
        log_lines = logs_info.get("log_lines", [])
        log_source = logs_info.get("source", f"logs/{service_name}.log")

        # Step 2: Analyze log patterns
        pattern_res = await self.kernel.invoke(
            plugin_name="LogTools",
            function_name="analyze_log_patterns",
            log_lines=log_lines,
            service_name=service_name
        )
        analysis = pattern_res.value

        evidence_items: List[EvidenceItem] = []
        now = datetime.now(timezone.utc).isoformat()

        if analysis.get("has_errors"):
            for i, p_info in enumerate(analysis.get("error_patterns", []), start=1):
                evidence_id = f"LOG-{incident_id[-3:] if len(incident_id) >= 3 else '001'}-{i:03d}"
                finding = f"{p_info['pattern_type']}: {p_info['count']} occurrences detected. Sample: {p_info['sample']}"
                
                item = EvidenceItem(
                    evidence_id=evidence_id,
                    agent="Logs Agent",
                    finding=finding,
                    service=service_name,
                    evidence_source=log_source,
                    evidence_timestamp=now,
                    raw_data={
                        "pattern_type": p_info["pattern_type"],
                        "count": p_info["count"],
                        "sample_log": p_info["sample"],
                        "total_errors": analysis.get("error_count", 0)
                    }
                )
                self.board.post_evidence(incident_id, item)
                evidence_items.append(item)
                logger.info(f"[Logs Agent] Posted evidence {evidence_id}: {p_info['pattern_type']}")
        else:
            # Record that logs were checked and no error patterns were found
            evidence_id = f"LOG-{incident_id[-3:] if len(incident_id) >= 3 else '001'}-001"
            item = EvidenceItem(
                evidence_id=evidence_id,
                agent="Logs Agent",
                finding=f"Analyzed {len(log_lines)} recent log lines for {service_name}. No error patterns or stack traces found.",
                service=service_name,
                evidence_source=log_source,
                evidence_timestamp=now,
                raw_data={"total_lines_analyzed": len(log_lines), "has_errors": False}
            )
            self.board.post_evidence(incident_id, item)
            evidence_items.append(item)
            logger.info(f"[Logs Agent] Posted baseline evidence {evidence_id}: clean logs")

        return evidence_items
