"""
Incident Commander Tools.
Provides evidence validation and traceable decision recording.
"""

from __future__ import annotations

from typing import Annotated, Any, Dict, List, Optional
from semantic_kernel.functions import kernel_function

from core.schemas import CommanderDecision, IncidentStatus


class CommanderTools:
    """Tools used by the Incident Commander."""

    @kernel_function(
        name="validate_evidence",
        description="Strictly validates that cited evidence IDs exist on the Blackboard and have authentic sources."
    )
    def validate_evidence(
        self,
        cited_evidence_ids: Annotated[List[str], "List of evidence IDs (e.g. LOG-001, DEP-001) cited in findings"],
        blackboard_evidence: Annotated[List[Dict[str, Any]], "List of all evidence records currently posted to Blackboard"]
    ) -> Dict[str, Any]:
        """
        Cross-checks every cited evidence ID against actual Blackboard evidence records.
        """
        board_ids = {e.get("evidence_id"): e for e in blackboard_evidence}
        valid_ids: List[str] = []
        missing_ids: List[str] = []
        evidence_details: List[Dict[str, Any]] = []

        for eid in cited_evidence_ids:
            if eid in board_ids:
                valid_ids.append(eid)
                ev = board_ids[eid]
                evidence_details.append({
                    "evidence_id": eid,
                    "agent": ev.get("agent"),
                    "finding": ev.get("finding"),
                    "source": ev.get("evidence_source")
                })
            else:
                missing_ids.append(eid)

        all_valid = (len(missing_ids) == 0) and (len(cited_evidence_ids) > 0)
        
        return {
            "all_valid": all_valid,
            "cited_count": len(cited_evidence_ids),
            "valid_count": len(valid_ids),
            "missing_count": len(missing_ids),
            "valid_ids": valid_ids,
            "missing_ids": missing_ids,
            "details": evidence_details,
            "validation_note": "All evidence IDs verified on Blackboard" if all_valid else f"Missing evidence IDs: {missing_ids}"
        }

    @kernel_function(
        name="record_incident_decision",
        description="Records the Incident Commander's validated root cause and mitigation decision."
    )
    def record_incident_decision(
        self,
        decision_data: Annotated[Dict[str, Any], "Decision payload containing root cause and recommendation"]
    ) -> Dict[str, Any]:
        """
        Validates decision structure, ensures recommendation-only status,
        and returns the validated decision structure.
        """
        required = ["incident_id", "likely_root_cause", "mitigation_decision", "decision_reason"]
        missing = [f for f in required if f not in decision_data or not decision_data[f]]
        if missing:
            return {
                "success": False,
                "error": f"Missing required decision fields: {', '.join(missing)}",
                "decision": None
            }

        # Ensure recommendation status
        decision_status = decision_data.get("decision_status", "recommended")
        if decision_status not in ("recommended", "escalated", "insufficient_evidence"):
            decision_status = "recommended"

        escalation_required = bool(decision_data.get("escalation_required", False))
        if decision_status in ("escalated", "insufficient_evidence"):
            escalation_required = True
            incident_status = IncidentStatus.ESCALATED
        else:
            incident_status = IncidentStatus.MITIGATING

        decision = CommanderDecision(
            incident_id=decision_data["incident_id"],
            likely_root_cause=decision_data["likely_root_cause"],
            root_cause_evidence=decision_data.get("root_cause_evidence", []),
            mitigation_decision=decision_data["mitigation_decision"],
            target_service=decision_data.get("target_service", "unknown"),
            decision_reason=decision_data["decision_reason"],
            decision_status=decision_status,
            incident_status=incident_status,
            confidence=float(decision_data.get("confidence", 0.85)),
            escalation_required=escalation_required
        )

        return {
            "success": True,
            "error": None,
            "decision": decision.model_dump()
        }


def validate_evidence(cited_evidence_ids: List[str], blackboard_evidence: List[Dict[str, Any]]) -> Dict[str, Any]:
    return CommanderTools().validate_evidence(cited_evidence_ids, blackboard_evidence)


def record_incident_decision(decision_data: Dict[str, Any]) -> Dict[str, Any]:
    return CommanderTools().record_incident_decision(decision_data)
