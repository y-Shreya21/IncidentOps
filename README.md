# AI IncidentOps: Autonomous Multi-Agent IT Incident Response War-Room

An autonomous, evidence-driven multi-agent incident response system designed to simulate an enterprise SRE war-room. Built on the **Blackboard Architecture** with **Microsoft Semantic Kernel / Agent Framework**, specialized agents collaborate asynchronously to ingest alerts, extract real log error patterns, probe dependency health topologies, match mitigation runbooks, enforce strict evidence validation, and compile postmortem reports.

---

## 1. Agent Roster & Responsibilities

The system consists of six specialized agents, each existing in its own Python module:

1. **Alert Agent (`agents/alert_agent.py`)**: Ingests incoming alerts, validates required schema fields, normalizes severity (`critical`, `high`, `medium`, `low`), enriches alerts with service ownership/tier metadata from the service registry, and initializes the incident on the Blackboard.
2. **Logs Agent (`agents/logs_agent.py`)**: Retrieves recent application logs from disk/containers for the affected service, executes deterministic regex pattern analysis (database timeouts, deployment stack traces, CPU saturation), and posts grounded `EvidenceItem` records with source filenames and timestamps.
3. **Dependency Agent (`agents/dependency_agent.py`)**: Traverses service dependency graphs from the topology registry, queries live HTTP health probes or simulated runtime state files, and posts dependency health evidence (`healthy` vs. `unhealthy`).
4. **Mitigation Agent (`agents/mitigation_agent.py`)**: Queries the operational runbook library based on detected log error signatures and symptoms, evaluates action preconditions and safety risks (`low`, `medium`, `high`), and posts `MitigationProposal` records.
5. **Incident Commander (`agents/incident_commander.py`)**: Final decision-making authority. Strictly cross-validates that every cited evidence ID exists on the Blackboard, calculates confidence scores, determines the probable root cause, issues binding mitigation recommendations, and triggers safe escalations.
6. **Communication Agent (`agents/communication_agent.py`)**: Formulates stakeholder status-page broadcasts grounded in confirmed Blackboard facts without making premature restoration claims.

---

## 2. Architecture & Why the Blackboard Fits

AI IncidentOps implements the **Blackboard Architectural Pattern** (`core/incident_board.py`). Rather than point-to-point peer agent messaging ($O(N^2)$ communication complexity), all agents communicate through a central, shared incident board backed by persistent storage and an append-only event log.

### Why Blackboard Fits IT Incident Response:
- **Single Source of Truth**: All agents share a consistent, synchronized view of incident telemetry, preventing conflicting local states.
- **Concurrent Execution**: Logs Agent and Dependency Agent execute in parallel via `asyncio.gather()`, posting findings independently without needing direct awareness of each other.
- **Evidence Traceability & Non-Hallucination**: The Incident Commander is constrained to make decisions exclusively using evidence IDs already registered on the Blackboard.
- **Immutable Audit Trail**: State transitions generate monotonic `TimelineEvent` records (`EVT-001`), ensuring full forensic auditability.

```
Incoming Alert ──► Alert Agent ──► [ SHARED BLACKBOARD ] ◄──► PostgreSQL / SQLite
                                          │
                  ┌───────────────────────┴───────────────────────┐
                  ▼                                               ▼
         Logs Agent (Parallel)                          Dependency Agent (Parallel)
                  │                                               │
                  └───────────────────────┬───────────────────────┘
                                          ▼
                               Mitigation Agent (Runbooks)
                                          ▼
                         Incident Commander (Evidence Validation)
                                          ▼
                        Communication Agent (Status Broadcasts)
```

---

## 3. Inventory of Agent Tools

Every working agent implements at least two genuine Python tools registered via Semantic Kernel `@kernel_function`:

| Agent | Python Tool Name | File Location | Purpose & Operation |
|---|---|---|---|
| **Alert Agent** | `validate_alert()` | `tools/alert_tools.py` | Validates schema fields; normalizes severity ratings. |
| **Alert Agent** | `lookup_service_metadata()` | `tools/alert_tools.py` | Queries service registry for tier, owner, and endpoints. |
| **Logs Agent** | `retrieve_recent_logs()` | `tools/log_tools.py` | Reads actual log lines from disk/container for the target service. |
| **Logs Agent** | `analyze_log_patterns()` | `tools/log_tools.py` | Regex pattern matching for database timeouts, crashes, and 5xx errors. |
| **Dependency Agent** | `retrieve_service_dependencies()` | `tools/dependency_tools.py` | Traverses dependency graph from `service_registry.json`. |
| **Dependency Agent** | `check_service_health()` | `tools/dependency_tools.py` | Probes live HTTP health endpoints or runtime simulation state. |
| **Mitigation Agent** | `retrieve_runbook()` | `tools/mitigation_tools.py` | Scans runbook catalog for matching remediation procedures. |
| **Mitigation Agent** | `evaluate_mitigation_preconditions()` | `tools/mitigation_tools.py` | Validates preconditions and risk levels against system evidence. |
| **Incident Commander** | `validate_evidence()` | `tools/commander_tools.py` | Cross-checks cited evidence IDs against actual Blackboard entries. |
| **Incident Commander** | `record_incident_decision()` | `tools/commander_tools.py` | Stores validated root cause, recommendation, and confidence score. |
| **Communication Agent** | `retrieve_status_template()` | `tools/communication_tools.py` | Fetches stakeholder templates based on severity and lifecycle status. |
| **Communication Agent** | `generate_status_update()` | `tools/communication_tools.py` | Builds verified status-page update avoiding false restoration claims. |

---

## 4. Memory and Retrieval Architecture

The system utilizes a structured, dual-tier persistence model:

1. **Relational Persistent Storage**: SQLite (`database/incidentops.db`) for zero-dependency local runs and pytest suites; PostgreSQL via SQLAlchemy ORM (`database/models.py`) for production container deployments. Maintains tables for `incidents`, `evidence`, `mitigation_proposals`, `decisions`, and `status_updates`.
2. **Append-Only Event Log (`core/event_logger.py`)**: An immutable, chronological audit trail recording every state change with monotonic sequence numbers, agent names, event types, payloads, and cited evidence IDs.
3. **Retrieval Mechanisms**: Runbook catalog retrieval (`infrastructure/runbooks/`) queries parameterized JSON remediation guides; service topology queries traverse `infrastructure/service_registry.json`.

---

## 5. Honest Failure Handled by the System

### Scenario D: Insufficient Evidence Handling (Safe Escalation)
A critical vulnerability in LLM-based operations is the temptation to hallucinate a root cause when data is incomplete or ambiguous. 

**Case Study**: A customer reports a vague latency anomaly. The war-room is triggered:
- **Logs Agent** inspects 150 lines of logs: clean logs, 0 error signatures, no stack traces.
- **Dependency Agent** probes all nodes: frontend, payment API, auth service, and database report 100% healthy.
- **Incident Commander Defense**: Rather than guessing a fictional failure or triggering a speculative service restart, the Commander detects that evidence is insufficient. It assigns a low confidence rating (0.35), issues a non-destructive `hold_and_escalate` decision, sets `escalation_required = true`, updates incident status to `ESCALATED`, and pings human on-call engineers for diagnostic triage. **Automated destructive actions are completely prevented.**

---

## 6. Execution & Verification Guide

### Prerequisites
- Python 3.11+
- Node.js 20+ (for React dashboard)
- Docker & Docker Compose (optional for containerized simulation)

### Running Automated Tests
Execute the full pytest suite (16 tests covering all unit tools, persistence, and failure scenarios):
```bash
python -m pytest -v
```

### Running the Backend API
```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```
API Documentation: `http://localhost:8000/docs` | Prometheus Metrics: `http://localhost:8000/metrics`

### Running the Operations Dashboard
- **React + Vite Dashboard (Recommended)**:
  ```bash
  cd frontend
  npm install
  npm run dev      # Opens at http://localhost:3000
  ```
- **Streamlit UI**:
  ```bash
  streamlit run frontend/dashboard.py
  ```

### Running the Demonstration Notebook
Open `notebooks/demo.ipynb` in VS Code or JupyterLab to view complete multi-agent execution traces across all failure scenarios.
