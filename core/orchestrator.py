"""
Orchestration Engine for AI IncidentOps.
Coordinates agent workflows around the shared Blackboard:
Alert Agent -> Concurrent(Logs Agent, Dependency Agent) -> Mitigation Agent -> Incident Commander -> Communication Agent.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, Optional

from core.incident_board import IncidentBoard
from core.schemas import IncidentState, PostmortemReport
from agents.alert_agent import AlertAgent
from agents.logs_agent import LogsAgent
from agents.dependency_agent import DependencyAgent
from agents.mitigation_agent import MitigationAgent
from agents.incident_commander import IncidentCommander
from agents.communication_agent import CommunicationAgent

logger = logging.getLogger("ai_incidentops.orchestrator")


class IncidentOrchestrator:
    """Orchestrates multi-agent incident response using Blackboard coordination."""

    def __init__(self, board: IncidentBoard, logs_dir: Optional[Path] = None):
        self.board = board
        self.logs_dir = logs_dir
        self.alert_agent = AlertAgent(board)
        self.logs_agent = LogsAgent(board, logs_dir=logs_dir)
        self.dependency_agent = DependencyAgent(board, logs_dir=logs_dir)
        self.mitigation_agent = MitigationAgent(board)
        self.commander = IncidentCommander(board)
        self.comm_agent = CommunicationAgent(board)

    async def run_incident_response(
        self,
        alert_payload: Dict[str, Any],
        enable_communication: bool = True
    ) -> PostmortemReport:
        """
        Executes complete multi-agent response cycle:
        1. Alert Agent ingests signal and initializes incident on Blackboard.
        2. Logs Agent and Dependency Agent execute concurrently via asyncio.gather.
        3. Mitigation Agent proposes recovery action based on posted findings.
        4. Incident Commander evaluates board, validates evidence, and records decision.
        5. Communication Agent publishes status updates.
        6. Generates final postmortem report.
        """
        logger.info("=== Starting AI IncidentOps War-Room Response Cycle ===")

        # Step 1: Alert Agent creates incident
        incident_state = await self.alert_agent.process_alert(alert_payload)
        incident_id = incident_state.incident_id
        logger.info(f"Step 1 Complete: Alert Agent initialized {incident_id}")

        # Step 2: Parallel Investigation (Logs Agent & Dependency Agent)
        logger.info("Step 2: Triggering parallel investigation (Logs & Dependency Agents)")
        logs_task = asyncio.create_task(self.logs_agent.investigate(incident_id))
        dep_task = asyncio.create_task(self.dependency_agent.investigate(incident_id))

        # Await completion of both investigative agents concurrently
        log_evidence, dep_evidence = await asyncio.gather(logs_task, dep_task, return_exceptions=False)
        logger.info(f"Step 2 Complete: Collected {len(log_evidence)} log findings and {len(dep_evidence)} dependency findings")

        # Step 3: Mitigation Agent proposes recovery action
        logger.info("Step 3: Triggering Mitigation Agent to evaluate runbooks")
        proposal = await self.mitigation_agent.propose_mitigation(incident_id)
        if proposal:
            logger.info(f"Step 3 Complete: Mitigation Agent proposed '{proposal.proposed_action}' on '{proposal.target_service}'")

        # Step 4: Incident Commander reviews board, validates evidence, decides root cause
        logger.info("Step 4: Incident Commander convening decision authority")
        decision = await self.commander.decide(incident_id)
        logger.info(f"Step 4 Complete: Commander decision '{decision.mitigation_decision}' (Confidence: {decision.confidence:.2f})")

        # Step 5: Communication Agent (Group-of-three extension)
        if enable_communication:
            logger.info("Step 5: Communication Agent broadcasting stakeholder update")
            await self.comm_agent.broadcast_status(incident_id)
            logger.info("Step 5 Complete: Stakeholder status update broadcasted")

        # Step 6: Generate final Postmortem Report
        postmortem = self.board.generate_postmortem(incident_id)
        if not postmortem:
            raise RuntimeError(f"Failed to generate postmortem for {incident_id}")

        logger.info(f"=== Response Cycle Complete for {incident_id} ===")
        return postmortem

    def get_incident_state(self, incident_id: str) -> Optional[IncidentState]:
        """Convenience method to retrieve full incident state."""
        return self.board.get_incident(incident_id)
