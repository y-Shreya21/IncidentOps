# ADR-003: Agent Framework Integration and Tool Sandboxing

## Status
Accepted

## Context
Production incident response demands deterministic accuracy for operational telemetry (reading actual logs, testing HTTP health probes). Unconstrained LLMs frequently hallucinate log snippets, fabricate dependency statuses, or generate dangerous shell commands if given raw execution access.

## Decision
1. **Agent Framework**: We utilize **Microsoft Semantic Kernel / Agent Framework**, exposing discrete tools registered via `@kernel_function` attributes.
2. **Deterministic Tool Execution**: All evidence collection, pattern extraction, health checks, and runbook searches are implemented as ordinary, deterministic Python functions.
3. **No Arbitrary Shell Access**: The LLM is restricted to analytical reasoning, pattern summarization, and hypothesis evaluation; it never has direct shell/CLI command execution privileges.
4. **Recommendation-Only Mitigation**: Mitigations remain strictly advisory until explicitly approved by an authenticated operator.

## Consequences
- Guaranteed reproducibility across all failure scenarios.
- Complete auditability and zero risk of destructive hallucinated commands.
