"""
Alert Agent Tools.
Provides alert validation and service registry lookup functions.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Any, Dict, Optional
from semantic_kernel.functions import kernel_function

from core.config import settings
from core.schemas import IncidentSeverity


class AlertTools:
    """Tools used by the Alert Agent."""

    def __init__(self, service_registry_path: Optional[Path] = None):
        self.registry_path = service_registry_path or settings.SERVICE_REGISTRY_PATH

    @kernel_function(
        name="validate_alert",
        description="Validates incoming alert payload fields and normalizes severity."
    )
    def validate_alert(
        self,
        alert_data: Annotated[Dict[str, Any], "Dictionary containing alert details"]
    ) -> Dict[str, Any]:
        """
        Validates required fields: service, symptom, severity, timestamp.
        Returns a dictionary with validation status and normalized fields.
        """
        required_fields = ["service", "symptom"]
        missing = [f for f in required_fields if f not in alert_data or not alert_data[f]]
        if missing:
            return {
                "valid": False,
                "error": f"Missing required alert fields: {', '.join(missing)}",
                "normalized_alert": None
            }

        # Normalize severity
        raw_sev = str(alert_data.get("severity", "high")).strip().lower()
        if raw_sev in ("critical", "crit", "sev-1", "p1"):
            severity = IncidentSeverity.CRITICAL
        elif raw_sev in ("high", "sev-2", "p2"):
            severity = IncidentSeverity.HIGH
        elif raw_sev in ("medium", "med", "sev-3", "p3"):
            severity = IncidentSeverity.MEDIUM
        else:
            severity = IncidentSeverity.LOW

        normalized = {
            "service": str(alert_data["service"]).strip(),
            "symptom": str(alert_data["symptom"]).strip(),
            "severity": severity.value,
            "timestamp": alert_data.get("timestamp", ""),
            "description": alert_data.get("description", alert_data["symptom"]),
            "incident_id": alert_data.get("incident_id")
        }

        return {
            "valid": True,
            "error": None,
            "normalized_alert": normalized
        }

    @kernel_function(
        name="lookup_service_metadata",
        description="Retrieves metadata and dependency topology for a service from the registry."
    )
    def lookup_service_metadata(
        self,
        service_name: Annotated[str, "Name of the service to look up"]
    ) -> Dict[str, Any]:
        """
        Queries the service registry file for service tier, owner, and endpoints.
        """
        if not self.registry_path.exists():
            return {
                "found": False,
                "error": f"Service registry file not found at {self.registry_path}",
                "metadata": None
            }

        try:
            with open(self.registry_path, "r", encoding="utf-8") as f:
                registry = json.load(f)
            
            services = registry.get("services", {})
            if service_name in services:
                return {
                    "found": True,
                    "error": None,
                    "metadata": services[service_name]
                }
            
            return {
                "found": False,
                "error": f"Service '{service_name}' not registered in service registry",
                "metadata": None
            }
        except Exception as e:
            return {
                "found": False,
                "error": f"Failed to read service registry: {str(e)}",
                "metadata": None
            }


# Standalone function aliases for standard Python invocations
def validate_alert(alert_data: Dict[str, Any]) -> Dict[str, Any]:
    return AlertTools().validate_alert(alert_data)


def lookup_service_metadata(service_name: str, registry_path: Optional[Path] = None) -> Dict[str, Any]:
    return AlertTools(registry_path).lookup_service_metadata(service_name)
