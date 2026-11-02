# Layer 9: Security & Threat Modeling Document

## 1. STRIDE Threat Model

| Threat Category | Threat Description | AI IncidentOps Defense Mechanism |
|---|---|---|
| **Spoofing** | Attacker impersonates an SRE operator to trigger fake incidents | JWT Bearer tokens signed with HMAC-SHA256; required claims validation (`sub`, `role`, `exp`). |
| **Tampering** | Rogue agent alters past evidence or historical decisions | Blackboard database enforces an **append-only event log**. Historical timeline events are immutable. |
| **Repudiation** | Operator denies approving a destructive mitigation | Human approvals require explicit confirmation recording operator username, timestamp, and audit event ID. |
| **Information Disclosure** | Sensitive database credentials or customer tokens leaked in logs | Sensitive log redaction regex; structured JSON logs strip authorization headers and passwords. |
| **Denial of Service** | Flooding alert webhook with fake incidents | `IdempotencyRegistry` rejects duplicate alerts within a 1-hour sliding TTL window. Rate limiting. |
| **Elevation of Privilege** | Read-only stakeholder attempts to trigger mitigation commands | Backend RBAC middleware (`require_roles([ROLE_ADMIN, ROLE_RESPONDER])`) blocks unauthorized API actions. |

---

## 2. Agent Security & Prompt Injection Defense

1. **Tool Execution Isolation**: Agents invoke discrete Python functions (`validate_alert`, `retrieve_recent_logs`, `check_service_health`). The LLM has zero direct shell, terminal, or arbitrary Python eval access.
2. **Untrusted Log Content**: Application logs ingested from monitored pods are treated as untrusted data. Deterministic regex pattern matching parses error codes directly, neutralizing log-based prompt injection payloads.
3. **Evidence Cross-Validation Invariant**: The Incident Commander validates that every cited `evidence_id` exists in the Blackboard database before accepting it. Hallucinated or injected evidence IDs are immediately rejected.
4. **Recommendation-Only Mitigation Default**: The Mitigation Agent only formulates structured recommendations; automated destructive execution is strictly prohibited.
