"""
Communication Agent Tools (Group-of-Three Extension).
Provides status-page template retrieval and verified stakeholder communication generation.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Annotated, Any, Dict, Optional
from semantic_kernel.functions import kernel_function

from core.schemas import IncidentSeverity, IncidentStatus, StatusUpdate


class CommunicationTools:
    """Tools used by the Communication Agent."""

    TEMPLATES = {
        "critical": {
            "investigating": {
                "headline": "Investigating Critical Outage in {service}",
                "template": "We are currently investigating a critical issue affecting {service} ({symptom}). Engineering teams are actively analyzing system logs and dependencies. Further updates will be provided within 15 minutes."
            },
            "mitigating": {
                "headline": "Mitigating Service Disruption in {service}",
                "template": "A mitigation plan ({action}) is currently underway for {service}. Technical teams are executing recovery runbooks to restore normal service operations."
            },
            "escalated": {
                "headline": "Critical Incident Escalated for {service}",
                "template": "The incident affecting {service} requires specialized escalation. SRE leads and service maintainers have been paged for manual war-room triage."
            },
            "resolved": {
                "headline": "Resolved: {service} Restored",
                "template": "The issue affecting {service} has been mitigated and verified healthy. All systems are operating normally."
            }
        },
        "high": {
            "investigating": {
                "headline": "Investigating Degradation in {service}",
                "template": "We are experiencing service degradation in {service} causing {symptom}. Our technical team is investigating logs and dependencies to identify the cause."
            },
            "mitigating": {
                "headline": "Applying Recovery Actions to {service}",
                "template": "Engineers have identified the probable cause and are applying recovery actions ({action}) to restore {service} performance."
            },
            "escalated": {
                "headline": "Escalation: {service} Under Extended Review",
                "template": "Investigation on {service} has been escalated to platform specialists to ensure complete diagnostic analysis."
            },
            "resolved": {
                "headline": "Resolved: Performance Restored for {service}",
                "template": "Performance metrics for {service} have returned to expected baselines. Monitoring continues."
            }
        },
        "medium": {
            "investigating": {
                "headline": "Monitoring Performance Anomaly in {service}",
                "template": "An anomaly ({symptom}) was detected in {service}. Engineers are investigating telemetry."
            },
            "mitigating": {
                "headline": "Remediating Anomaly in {service}",
                "template": "Remediation step ({action}) is being executed for {service}."
            },
            "escalated": {
                "headline": "Follow-up Escalation for {service}",
                "template": "Service anomaly in {service} flagged for next-tier maintenance team review."
            },
            "resolved": {
                "headline": "Resolved: {service} Operating Normally",
                "template": "The anomaly in {service} has been resolved."
            }
        }
    }

    @kernel_function(
        name="retrieve_status_template",
        description="Retrieves the appropriate stakeholder status communication template based on severity and lifecycle status."
    )
    def retrieve_status_template(
        self,
        severity: Annotated[str, "Incident severity level: critical, high, medium, low"],
        status: Annotated[str, "Incident lifecycle status: investigating, mitigating, escalated, resolved"]
    ) -> Dict[str, Any]:
        """
        Selects template based on severity and incident status.
        """
        sev_key = severity.lower() if severity.lower() in self.TEMPLATES else "high"
        stat_key = status.lower() if status.lower() in self.TEMPLATES[sev_key] else "investigating"

        entry = self.TEMPLATES[sev_key][stat_key]
        return {
            "severity": sev_key,
            "status": stat_key,
            "headline_template": entry["headline"],
            "message_template": entry["template"]
        }

    @kernel_function(
        name="generate_status_update",
        description="Generates an accurate, verified stakeholder status update avoiding false restoration claims."
    )
    def generate_status_update(
        self,
        incident_id: Annotated[str, "Incident identifier"],
        service_name: Annotated[str, "Affected service name"],
        symptom: Annotated[str, "Observed symptom"],
        severity: Annotated[str, "Incident severity"],
        status: Annotated[str, "Current incident status"],
        action: Annotated[str, "Proposed or active mitigation action"] = "investigation"
    ) -> Dict[str, Any]:
        """
        Builds a StatusUpdate object using verified incident facts.
        """
        template_info = self.retrieve_status_template(severity, status)
        
        headline = template_info["headline_template"].format(service=service_name)
        message = template_info["message_template"].format(
            service=service_name,
            symptom=symptom,
            action=action
        )

        update_id = f"UPD-{uuid.uuid4().hex[:6].upper()}"
        now = datetime.now(timezone.utc).isoformat()

        # Strictly enforce: never claim resolved if status is not resolved
        if status.lower() != "resolved" and ("resolved" in message.lower() or "restored" in message.lower()):
            message = f"Technical teams are actively mitigating the issue affecting {service_name}. Monitoring continues."

        update = StatusUpdate(
            update_id=update_id,
            incident_id=incident_id,
            severity=IncidentSeverity(template_info["severity"]),
            status=IncidentStatus(template_info["status"]),
            timestamp=now,
            headline=headline,
            message=message,
            audience="public"
        )

        return {
            "success": True,
            "status_update": update.model_dump()
        }


def retrieve_status_template(severity: str, status: str) -> Dict[str, Any]:
    return CommunicationTools().retrieve_status_template(severity, status)


def generate_status_update(incident_id: str, service_name: str, symptom: str, severity: str, status: str, action: str = "investigation") -> Dict[str, Any]:
    return CommunicationTools().generate_status_update(incident_id, service_name, symptom, severity, status, action)

