# Layer 2: System Architecture Document
## AI IncidentOps: Multi-Agent IT Incident Response War-Room

---

## 1. High-Level Architecture Overview

The system implements the **Blackboard Architectural Pattern**. Rather than agents passing ad-hoc messages directly to one another in a point-to-point fashion, all agents read from and write to a single source of truth: the **Shared Incident Board**.

```mermaid
flowchart TB
    subgraph Ingestion ["Ingestion Layer"]
        Alert["Incoming Alert (REST / Webhook)"]
    end

    subgraph Orchestration ["Agent Orchestration Layer"]
        Orch["IncidentOrchestrator"]
    end

    subgraph Agents ["Specialized AI Agents"]
        AA["1. Alert Agent"]
        LA["2. Logs Agent"]
        DA["3. Dependency Agent"]
        MA["4. Mitigation Agent"]
        IC["5. Incident Commander"]
        CA["6. Communication Agent"]
    end

    subgraph Blackboard ["Central Blackboard (IncidentBoard)"]
        State["Active Incident State"]
        EvidenceReg["Evidence Registry (LOG-xxx, DEP-xxx)"]
        PropReg["Mitigation Proposals"]
        DecisionReg["Commander Decisions"]
        Timeline["Append-Only Event Log (EVT-xxx)"]
    end

    subgraph Storage ["Persistence Layer"]
        DB[(PostgreSQL / SQLite Storage)]
    end

    subgraph Presentation ["Presentation Layer"]
        ReactUI["React + TypeScript Operations Dashboard"]
        StreamlitUI["Streamlit Rapid Operations UI"]
        API["FastAPI REST Endpoints"]
    end

    Alert --> API
    API --> Orch
    Orch --> AA
    AA -->|Validate & Register| Blackboard
    Orch -->|Concurrent Trigger| LA
    Orch -->|Concurrent Trigger| DA
    LA -->|Post Log Evidence| Blackboard
    DA -->|Post Health Evidence| Blackboard
    Blackboard -->|Read Evidence| MA
    MA -->|Post Proposal| Blackboard
    Blackboard -->|Inspect & Validate| IC
    IC -->|Record Binding Decision| Blackboard
    Blackboard -->|Read Verified Facts| CA
    CA -->|Broadcast Status Update| Blackboard
    Blackboard <--> DB
    Presentation <--> API
    API <--> Blackboard
```

---

## 2. Low-Level Component Architecture

### 2.1 The Shared Blackboard (`core/incident_board.py`)
The Blackboard encapsulates all incident state modifications:
- **Thread Safety**: Inter-process and intra-process concurrency protection via `threading.Lock` and ACID database transactions.
- **Append-Only Event Log (`core/event_logger.py`)**: Every agent invocation, evidence registration, status change, and decision appends an immutable `TimelineEvent` record with an auto-incrementing monotonic sequence.
- **Data Integrity**: State cannot be mutated arbitrarily; transitions follow the lifecycle:
  $$\text{INVESTIGATING} \longrightarrow \text{MITIGATING} \longrightarrow \text{MITIGATED / RESOLVED}$$
  $$\text{INVESTIGATING} \longrightarrow \text{ESCALATED}$$

### 2.2 Agent Module Boundaries & Tool Contracts

Each agent operates inside its own module and executes tools through **Microsoft Semantic Kernel / Agent Framework**:

```mermaid
classDiagram
    class IncidentBoard {
        +create_incident(service, symptom, severity)
        +get_incident(incident_id)
        +post_evidence(incident_id, evidence)
        +post_mitigation_proposal(incident_id, proposal)
        +record_decision(incident_id, decision)
        +post_status_update(incident_id, update)
        +generate_postmortem(incident_id)
    }

    class AlertAgent {
        +process_alert(alert_data)
    }

    class LogsAgent {
        +investigate(incident_id)
    }

    class DependencyAgent {
        +investigate(incident_id)
    }

    class MitigationAgent {
        +propose_mitigation(incident_id)
    }

    class IncidentCommander {
        +decide(incident_id)
    }

    class CommunicationAgent {
        +broadcast_status(incident_id)
    }

    AlertAgent --> IncidentBoard : reads & writes
    LogsAgent --> IncidentBoard : reads & writes
    DependencyAgent --> IncidentBoard : reads & writes
    MitigationAgent --> IncidentBoard : reads & writes
    IncidentCommander --> IncidentBoard : reads & writes
    CommunicationAgent --> IncidentBoard : reads & writes
```

---

## 3. Orchestration Sequence Diagram

```mermaid
sequenceDiagram
    autonumber
    actor Operator as SRE / Webhook
    participant Orch as Orchestrator
    participant AlertAg as Alert Agent
    participant LogsAg as Logs Agent
    participant DepAg as Dependency Agent
    participant MitAg as Mitigation Agent
    participant Cmdr as Incident Commander
    participant CommAg as Communication Agent
    participant Board as Shared Blackboard (DB)

    Operator->>Orch: Submit Incident Alert
    Orch->>AlertAg: process_alert(payload)
    AlertAg->>AlertAg: validate_alert() & lookup_service_metadata()
    AlertAg->>Board: create_incident(service, symptom, severity)
    Board-->>AlertAg: Incident INC-001 initialized
    
    par Parallel Investigation
        Orch->>LogsAg: investigate(INC-001)
        LogsAg->>LogsAg: retrieve_recent_logs() & analyze_log_patterns()
        LogsAg->>Board: post_evidence(LOG-001: DB Connection Timeout)
    and
        Orch->>DepAg: investigate(INC-001)
        DepAg->>DepAg: retrieve_dependencies() & check_service_health()
        DepAg->>Board: post_evidence(DEP-001: Postgres Unhealthy)
    end

    Orch->>MitAg: propose_mitigation(INC-001)
    MitAg->>Board: Read all evidence (LOG-001, DEP-001)
    MitAg->>MitAg: retrieve_runbook() & evaluate_preconditions()
    MitAg->>Board: post_mitigation_proposal(PROP-001: restart postgres)

    Orch->>Cmdr: decide(INC-001)
    Cmdr->>Board: Inspect entire Blackboard state
    Cmdr->>Cmdr: validate_evidence([LOG-001, DEP-001])
    Cmdr->>Cmdr: determine_root_cause()
    Cmdr->>Board: record_decision(Decision: restart postgres, Confidence: 0.92)

    opt Communication Extension Enabled
        Orch->>CommAg: broadcast_status(INC-001)
        CommAg->>Board: Read confirmed state
        CommAg->>CommAg: retrieve_template() & generate_update()
        CommAg->>Board: post_status_update(UPD-001)
    end

    Orch->>Board: generate_postmortem(INC-001)
    Board-->>Orch: Complete Postmortem Report
    Orch-->>Operator: Return Postmortem & Incident State
```

---

## 4. Architectural Invariants & Safety Guarantees

1. **Strict Evidence Grounding**: The Incident Commander's root cause must reference valid `evidence_id` tokens previously recorded on the Blackboard. Hallucinated IDs are caught by `validate_evidence()`.
2. **Recommendation-Only Default**: Automated destructive actions (container deletion, DB restart, deployment rollback) are never triggered without human approval.
3. **Safe Escalation**: When evidence is missing or ambiguous (Scenario D), the system issues a `hold_and_escalate` decision rather than guessing.
4. **Append-Only Auditing**: Every state change produces an immutable event log record with ISO-8601 timestamp and monotonic sequence.
