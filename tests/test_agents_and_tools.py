"""
Unit Tests for Agent Tools and Individual Agent Behaviors.
Verifies all 12 Python tools across the 6 agents.
"""

import pytest
from pathlib import Path
from tools.alert_tools import AlertTools, validate_alert, lookup_service_metadata
from tools.log_tools import LogTools, retrieve_recent_logs, analyze_log_patterns
from tools.dependency_tools import DependencyTools, retrieve_service_dependencies, check_service_health
from tools.mitigation_tools import MitigationTools, retrieve_runbook, evaluate_mitigation_preconditions
from tools.commander_tools import CommanderTools, validate_evidence, record_incident_decision
from tools.communication_tools import CommunicationTools, retrieve_status_template, generate_status_update


def test_alert_tools():
    # 1. validate_alert
    val_valid = validate_alert({"service": "payment-api", "symptom": "500 errors", "severity": "CRITICAL"})
    assert val_valid["valid"] is True
    assert val_valid["normalized_alert"]["severity"] == "critical"

    val_invalid = validate_alert({"service": "", "symptom": ""})
    assert val_invalid["valid"] is False

    # 2. lookup_service_metadata
    meta = lookup_service_metadata("payment-api")
    assert meta["found"] is True
    assert "postgres" in meta["metadata"]["dependencies"]


def test_log_tools(tmp_path: Path):
    log_file = tmp_path / "test-service.log"
    with open(log_file, "w") as f:
        f.write("2026-11-02 10:00:00 [INFO] Started\n")
        f.write("2026-11-02 10:01:00 [ERROR] psycopg2.OperationalError: connection timeout to db\n")

    log_tools = LogTools(logs_dir=tmp_path)
    
    # 1. retrieve_recent_logs
    res = log_tools.retrieve_recent_logs("test-service", max_lines=10)
    assert res["success"] is True
    assert len(res["log_lines"]) == 2

    # 2. analyze_log_patterns
    analysis = log_tools.analyze_log_patterns(res["log_lines"], service_name="test-service")
    assert analysis["has_errors"] is True
    assert analysis["primary_pattern"] == "database_connection_timeout"


def test_dependency_tools(tmp_path: Path):
    dep_tools = DependencyTools()
    
    # 1. retrieve_service_dependencies
    deps = dep_tools.retrieve_service_dependencies("payment-api")
    assert deps["success"] is True
    assert "postgres" in deps["dependencies"]

    # 2. check_service_health fallback
    health = dep_tools.check_service_health("payment-api")
    assert health["status"] in ("healthy", "unhealthy")


def test_mitigation_tools():
    mit_tools = MitigationTools()

    # 1. retrieve_runbook
    rb = mit_tools.retrieve_runbook("database connection timeout")
    assert rb["found"] is True
    assert rb["runbook"]["recommended_action"] == "restart"

    # 2. evaluate_mitigation_preconditions
    precond = mit_tools.evaluate_mitigation_preconditions(
        action="rollback",
        target_service="payment-api",
        evidence_summary={"primary_pattern": "deployment_bug_crash", "has_log_errors": True}
    )
    assert precond["preconditions_met"] is True
    assert precond["action"] == "rollback"


def test_commander_tools():
    cmd_tools = CommanderTools()

    # 1. validate_evidence
    board_evidence = [
        {"evidence_id": "LOG-001", "agent": "Logs Agent", "finding": "DB Timeout", "evidence_source": "log"}
    ]
    val_ok = cmd_tools.validate_evidence(["LOG-001"], board_evidence)
    assert val_ok["all_valid"] is True

    val_fake = cmd_tools.validate_evidence(["FAKE-001"], board_evidence)
    assert val_fake["all_valid"] is False
    assert "FAKE-001" in val_fake["missing_ids"]

    # 2. record_incident_decision
    dec = cmd_tools.record_incident_decision({
        "incident_id": "INC-001",
        "likely_root_cause": "DB Failure",
        "mitigation_decision": "restart",
        "target_service": "postgres",
        "decision_reason": "Logs and health check fail",
        "confidence": 0.90
    })
    assert dec["success"] is True
    assert dec["decision"]["decision_status"] == "recommended"


def test_communication_tools():
    comm_tools = CommunicationTools()

    # 1. retrieve_status_template
    tmpl = comm_tools.retrieve_status_template("critical", "investigating")
    assert "critical" in tmpl["severity"]
    assert "{service}" in tmpl["headline_template"]

    # 2. generate_status_update
    upd = comm_tools.generate_status_update(
        incident_id="INC-001",
        service_name="payment-api",
        symptom="500 errors",
        severity="critical",
        status="investigating"
    )
    assert upd["success"] is True
    assert "payment-api" in upd["status_update"]["message"]
    # Verify no false restoration claim
    assert "restored" not in upd["status_update"]["message"].lower() or upd["status_update"]["status"] == "resolved"
