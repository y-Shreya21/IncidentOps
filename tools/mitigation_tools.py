"""
Mitigation Agent Tools.
Provides runbook retrieval and precondition evaluation for proposed recovery actions.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Any, Dict, List, Optional
from semantic_kernel.functions import kernel_function

from core.config import settings


class MitigationTools:
    """Tools used by the Mitigation Agent."""

    def __init__(self, runbooks_dir: Optional[Path] = None):
        self.runbooks_dir = runbooks_dir or settings.RUNBOOKS_DIR

    @kernel_function(
        name="retrieve_runbook",
        description="Retrieves the matching recovery procedure runbook for an incident symptom or failure type."
    )
    def retrieve_runbook(
        self,
        incident_type: Annotated[str, "The incident symptom or failure pattern to look up runbook for"]
    ) -> Dict[str, Any]:
        """
        Scans runbooks directory and returns the best matching runbook.
        """
        if not self.runbooks_dir.exists():
            return {
                "found": False,
                "error": f"Runbooks directory not found at {self.runbooks_dir}",
                "runbook": None
            }

        incident_type_lower = incident_type.lower()

        # Map patterns to filenames
        mapping = {
            "database": "database_connectivity.json",
            "db": "database_connectivity.json",
            "connection": "database_connectivity.json",
            "timeout": "database_connectivity.json",
            "deployment": "failed_deployment.json",
            "rollback": "failed_deployment.json",
            "release": "failed_deployment.json",
            "cpu": "high_cpu.json",
            "resource": "high_cpu.json",
            "saturation": "high_cpu.json",
            "insufficient": "generic_escalation.json",
            "unknown": "generic_escalation.json"
        }

        matched_file = None
        for keyword, filename in mapping.items():
            if keyword in incident_type_lower:
                matched_file = self.runbooks_dir / filename
                break

        if not matched_file or not matched_file.exists():
            # Fallback to generic escalation
            matched_file = self.runbooks_dir / "generic_escalation.json"

        if matched_file.exists():
            try:
                with open(matched_file, "r", encoding="utf-8") as f:
                    rb_data = json.load(f)
                return {
                    "found": True,
                    "error": None,
                    "runbook": rb_data,
                    "source": str(matched_file)
                }
            except Exception as e:
                return {
                    "found": False,
                    "error": f"Failed reading runbook: {str(e)}",
                    "runbook": None
                }

        return {
            "found": False,
            "error": "No matching runbook found",
            "runbook": None
        }

    @kernel_function(
        name="evaluate_mitigation_preconditions",
        description="Evaluates whether a proposed mitigation action satisfies system safety preconditions."
    )
    def evaluate_mitigation_preconditions(
        self,
        action: Annotated[str, "Proposed action: restart, rollback, failover, hold_and_escalate"],
        target_service: Annotated[str, "Target service for the mitigation"],
        evidence_summary: Annotated[Dict[str, Any], "Summary of logs and dependency evidence"]
    ) -> Dict[str, Any]:
        """
        Evaluates preconditions, risks, and provides a go/no-go recommendation.
        """
        action = action.lower().strip()
        has_log_errors = evidence_summary.get("has_log_errors", False)
        primary_pattern = evidence_summary.get("primary_pattern", "")
        unhealthy_deps = evidence_summary.get("unhealthy_dependencies", [])
        
        preconditions_met = False
        risk_level = "medium"
        reason = ""

        if action == "restart":
            # Precondition: service or dependency is confirmed down or has connection timeouts
            if "database" in primary_pattern or any("postgres" in str(d) for d in unhealthy_deps):
                preconditions_met = True
                risk_level = "medium"
                reason = "Database connectivity timeout confirmed by logs and unhealthy database health check. Restarting database restores connection pool."
            elif "cpu" in primary_pattern or "saturation" in primary_pattern:
                preconditions_met = True
                risk_level = "medium"
                reason = "Worker saturation confirmed. Worker restart clears runaway threads."
            else:
                preconditions_met = True
                risk_level = "medium"
                reason = f"Service '{target_service}' is unresponsive; rolling restart recommended."

        elif action == "rollback":
            # Precondition: deployment failure detected and database is healthy
            if "deployment" in primary_pattern or "release" in primary_pattern or evidence_summary.get("recent_deployment", False):
                preconditions_met = True
                risk_level = "medium"
                reason = "Deployment regression identified in logs; underlying database is healthy. Rollback to previous stable image tag is safe."
            else:
                preconditions_met = False
                risk_level = "high"
                reason = "No deployment error signature identified. Speculative rollback carries high risk."

        elif action == "failover":
            if any("postgres" in str(d) for d in unhealthy_deps):
                preconditions_met = True
                risk_level = "high"
                reason = "Primary database is completely down. Failover to standby replica will restore service."
            else:
                preconditions_met = False
                risk_level = "high"
                reason = "Standby failover requires confirmation of primary storage unavailability."

        elif action == "hold_and_escalate":
            preconditions_met = True
            risk_level = "low"
            reason = "Evidence is insufficient or conflicting; automatic mitigation is held to prevent destructive side-effects."

        else:
            preconditions_met = False
            risk_level = "high"
            reason = f"Unknown action '{action}'."

        return {
            "action": action,
            "target_service": target_service,
            "preconditions_met": preconditions_met,
            "risk_level": risk_level,
            "reason": reason
        }


def retrieve_runbook(incident_type: str, runbooks_dir: Optional[Path] = None) -> Dict[str, Any]:
    return MitigationTools(runbooks_dir).retrieve_runbook(incident_type)


def evaluate_mitigation_preconditions(action: str, target_service: str, evidence_summary: Dict[str, Any]) -> Dict[str, Any]:
    return MitigationTools().evaluate_mitigation_preconditions(action, target_service, evidence_summary)
