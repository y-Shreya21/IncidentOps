"""
Streamlit Dashboard for AI IncidentOps: Autonomous Multi-Agent IT Incident Response War-Room.
Displays real-time incident state, agent activity, blackboard contents, timelines, and postmortems.
"""

from __future__ import annotations

import asyncio
import json
import streamlit as st
from datetime import datetime, timezone
from pathlib import Path

# Adjust path so imports work when running `streamlit run frontend/dashboard.py`
import sys
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from core.config import settings
from core.incident_board import IncidentBoard
from core.orchestrator import IncidentOrchestrator
from core.schemas import IncidentSeverity, IncidentStatus
from infrastructure.simulation_runner import simulation

st.set_page_config(
    page_title="AI IncidentOps War-Room",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize shared components
@st.cache_resource
def get_backend():
    board = IncidentBoard(settings.DB_PATH)
    orchestrator = IncidentOrchestrator(board)
    return board, orchestrator

board, orchestrator = get_backend()

# Custom Styling
st.markdown("""
<style>
    .reportview-container { background: #0e1117; }
    .metric-card {
        background-color: #1f2937;
        padding: 18px;
        border-radius: 10px;
        border-left: 5px solid #3b82f6;
        margin-bottom: 12px;
    }
    .badge-critical { color: #f87171; font-weight: bold; }
    .badge-high { color: #fb923c; font-weight: bold; }
    .badge-medium { color: #facc15; font-weight: bold; }
    .badge-low { color: #4ade80; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.title("🛡️ AI IncidentOps: Autonomous Multi-Agent War-Room")
st.caption("Blackboard Architecture • Semantic Kernel • Evidence-Driven Incident Response")

# Sidebar: Controls & Incident Selection
st.sidebar.header("Incident Management")
incidents = board.list_incidents()
incident_ids = [inc.incident_id for inc in incidents] if incidents else []

selected_inc_id = None
if incident_ids:
    selected_inc_id = st.sidebar.selectbox("Select Active Incident", options=incident_ids, index=0)
else:
    st.sidebar.info("No incidents recorded yet. Create or simulate one below.")

st.sidebar.divider()
st.sidebar.subheader("Quick Scenario Simulator")
st.sidebar.caption("Trigger realistic local failure scenarios:")

col_sim1, col_sim2 = st.sidebar.columns(2)
with col_sim1:
    if st.button("💥 DB Failure", use_container_width=True):
        with st.spinner("Simulating PostgreSQL outage & running war-room..."):
            alert = simulation.setup_database_failure()
            report = asyncio.run(orchestrator.run_incident_response(alert))
            st.sidebar.success(f"Incident {report.incident_id} created!")
            st.rerun()

    if st.button("🚀 Bad Release", use_container_width=True):
        with st.spinner("Simulating deployment regression & running war-room..."):
            alert = simulation.setup_deployment_failure()
            report = asyncio.run(orchestrator.run_incident_response(alert))
            st.sidebar.success(f"Incident {report.incident_id} created!")
            st.rerun()

with col_sim2:
    if st.button("🔥 High CPU", use_container_width=True):
        with st.spinner("Simulating worker saturation & running war-room..."):
            alert = simulation.setup_high_cpu()
            report = asyncio.run(orchestrator.run_incident_response(alert))
            st.sidebar.success(f"Incident {report.incident_id} created!")
            st.rerun()

    if st.button("❓ Insufficient", use_container_width=True):
        with st.spinner("Simulating ambiguous blip & running war-room..."):
            alert = simulation.setup_insufficient_evidence()
            report = asyncio.run(orchestrator.run_incident_response(alert))
            st.sidebar.success(f"Incident {report.incident_id} created!")
            st.rerun()

st.sidebar.divider()
if st.sidebar.button("🔄 Reset All Simulations", use_container_width=True):
    simulation.reset()
    st.sidebar.info("Simulation environment reset to healthy state.")

# ----------------- SECTION A: Incident Overview -----------------
st.subheader("📊 System Overview")
col1, col2, col3, col4 = st.columns(4)

total_incidents = len(incidents)
crit_count = sum(1 for inc in incidents if inc.severity == IncidentSeverity.CRITICAL)
high_count = sum(1 for inc in incidents if inc.severity == IncidentSeverity.HIGH)
escalated_count = sum(1 for inc in incidents if inc.status == IncidentStatus.ESCALATED)

col1.metric("Total Incidents", total_incidents)
col2.metric("Critical Incidents", crit_count)
col3.metric("High Severity", high_count)
col4.metric("Escalated Incidents", escalated_count)

st.divider()

# Tab Layout for Main Features
tab_board, tab_agents, tab_decision, tab_timeline, tab_postmortem, tab_comm, tab_create = st.tabs([
    "📋 Blackboard Viewer",
    "🤖 Agent Activity",
    "⚖️ Mitigation Decision",
    "⏱️ Event Timeline",
    "📄 Postmortem Report",
    "📢 Status Communication",
    "➕ Ingest Alert"
])

current_incident = board.get_incident(selected_inc_id) if selected_inc_id else None

# ----------------- SECTION B: Create Incident -----------------
with tab_create:
    st.subheader("Ingest New Alert")
    with st.form("create_incident_form"):
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            service_input = st.selectbox(
                "Affected Service",
                ["payment-api", "frontend", "auth-service", "postgres"]
            )
            severity_input = st.selectbox(
                "Severity",
                ["critical", "high", "medium", "low"]
            )
        with col_s2:
            symptom_input = st.text_input("Incident Symptom", "HTTP 500 Internal Server Errors")
            timestamp_input = st.text_input("Timestamp", datetime.now(timezone.utc).isoformat())

        description_input = st.text_area(
            "Incident Description",
            "Checkout API responding with 500 errors after automated canary rollout."
        )

        submit_alert = st.form_submit_button("🚀 Submit Alert to War-Room")
        if submit_alert:
            alert_payload = {
                "service": service_input,
                "symptom": symptom_input,
                "severity": severity_input,
                "timestamp": timestamp_input,
                "description": description_input
            }
            with st.spinner("Orchestrating multi-agent response..."):
                report = asyncio.run(orchestrator.run_incident_response(alert_payload))
                st.success(f"Incident {report.incident_id} successfully investigated and decided!")
                st.rerun()

if not current_incident:
    st.info("👈 Please trigger a simulation scenario or submit an alert to populate the war-room.")
    st.stop()
    raise SystemExit(0)

# ----------------- SECTION D: Blackboard Viewer -----------------
with tab_board:
    st.subheader(f"Blackboard State: {current_incident.incident_id}")
    
    col_meta1, col_meta2, col_meta3, col_meta4 = st.columns(4)
    col_meta1.markdown(f"**Service:** `{current_incident.service}`")
    col_meta2.markdown(f"**Severity:** `{current_incident.severity.value.upper()}`")
    col_meta3.markdown(f"**Status:** `{current_incident.status.value.upper()}`")
    col_meta4.markdown(f"**Escalation:** `{current_incident.escalation_status.upper()}`")
    
    st.markdown(f"**Symptom:** {current_incident.symptom}")
    st.markdown(f"**Description:** {current_incident.description}")
    
    st.markdown("#### Evidence Registry (Strict Grounding)")
    if current_incident.evidence:
        for ev in current_incident.evidence:
            with st.expander(f"📌 [{ev.evidence_id}] {ev.agent} — {ev.finding[:80]}..."):
                st.markdown(f"**Agent:** {ev.agent}")
                st.markdown(f"**Finding:** {ev.finding}")
                st.markdown(f"**Service:** `{ev.service}`")
                st.markdown(f"**Evidence Source:** `{ev.evidence_source}`")
                st.markdown(f"**Timestamp:** `{ev.evidence_timestamp}`")
                st.json(ev.raw_data)
    else:
        st.write("No evidence posted yet.")

    st.markdown("#### Mitigation Proposals on Board")
    if current_incident.mitigation_proposals:
        for prop in current_incident.mitigation_proposals:
            st.info(
                f"**[{prop.proposal_id}] Proposed Action:** `{prop.proposed_action.upper()}` on `{prop.target_service}`\n\n"
                f"**Risk Level:** {prop.risk_level.upper()} | **Reason:** {prop.reason}\n\n"
                f"**Supporting Evidence:** {', '.join(prop.supporting_evidence)}"
            )

# ----------------- SECTION C: Agent Activity -----------------
with tab_agents:
    st.subheader("Agent Operations & Tool Traces")
    
    agents_info = [
        ("🚨 Alert Agent", "Ingested signal, validated schema, queried service registry.", "tools/alert_tools.py"),
        ("📜 Logs Agent", "Retrieved actual application logs, performed deterministic regex pattern parsing.", "tools/log_tools.py"),
        ("🔗 Dependency Agent", "Traversed topology, queried health probes for upstream/downstream services.", "tools/dependency_tools.py"),
        ("🛠️ Mitigation Agent", "Queried runbooks library, validated preconditions against evidence.", "tools/mitigation_tools.py"),
        ("⚖️ Incident Commander", "Cross-validated cited evidence IDs, determined root cause, issued binding recommendation.", "tools/commander_tools.py"),
        ("📢 Communication Agent", "Drafted stakeholder status update without false resolution claims.", "tools/communication_tools.py"),
    ]

    for name, desc, tool_file in agents_info:
        with st.container():
            st.markdown(f"### {name}")
            st.markdown(f"*{desc}*")
            st.caption(f"Underlying Tools: `{tool_file}`")
            
            # Show events generated by this agent
            agent_events = [ev for ev in current_incident.timeline if ev.agent.lower() in name.lower()]
            if agent_events:
                for evt in agent_events:
                    st.write(f"• `{evt.timestamp}`: **{evt.event_type}** — Evidence Cited: `{evt.evidence_ids}`")
            st.divider()

# ----------------- SECTION E: Mitigation Decision -----------------
with tab_decision:
    st.subheader("Incident Commander Decision")
    
    dec = current_incident.decision
    if dec:
        if dec.decision_status == "insufficient_evidence":
            st.error("⚠️ INSUFFICIENT EVIDENCE DETECTED — ESCALATION REQUIRED")
        else:
            st.success(f"DECISION STATUS: {dec.decision_status.upper()}")

        col_d1, col_d2 = st.columns(2)
        with col_d1:
            st.markdown(f"**Likely Root Cause:**\n### {dec.likely_root_cause}")
            st.markdown(f"**Target Service:** `{dec.target_service}`")
            st.markdown(f"**Mitigation Decision:** `{dec.mitigation_decision.upper()}`")
            st.metric("Confidence Score", f"{dec.confidence * 100:.1f}%")

        with col_d2:
            st.markdown("**Evidence Citations (Strict Validation):**")
            for eid in dec.root_cause_evidence:
                st.code(eid, language="text")
            st.markdown(f"**Decision Rationale:**\n\n{dec.decision_reason}")
            st.markdown(f"**Escalation Required:** `{dec.escalation_required}`")
    else:
        st.warning("Incident Commander has not finalized a decision yet.")

# ----------------- SECTION F: Incident Timeline -----------------
with tab_timeline:
    st.subheader("Chronological Event Log (Append-Only)")
    
    timeline = current_incident.timeline
    if timeline:
        for ev in timeline:
            with st.container():
                st.markdown(
                    f"**`{ev.timestamp}`** | **{ev.agent}** | `{ev.event_type}` | Event ID: `{ev.event_id}`"
                )
                if ev.evidence_ids:
                    st.caption(f"Cited Evidence: {', '.join(ev.evidence_ids)}")
                if ev.payload:
                    st.json(ev.payload)
                st.divider()
    else:
        st.write("No timeline events recorded.")

# ----------------- SECTION G: Postmortem Report -----------------
with tab_postmortem:
    st.subheader("Structured Postmortem Report")
    
    pm = board.generate_postmortem(current_incident.incident_id)
    if pm:
        md_report = f"""
# Postmortem Report: {pm.incident_id}
**Service:** {pm.affected_service}  
**Severity:** {pm.severity.value.upper()}  
**Status:** {pm.final_incident_status.value.upper()}  
**Generated At:** {pm.generated_at}  

---

## 1. Incident Summary
{pm.incident_description}

## 2. Root Cause Analysis
- **Likely Root Cause:** {pm.likely_root_cause}
- **Supporting Evidence Citations:** {', '.join(pm.root_cause_evidence)}

## 3. Investigative Findings
### Logs Agent Findings
{chr(10).join(f"- {f}" for f in pm.logs_findings) if pm.logs_findings else "- No error patterns detected."}

### Dependency Agent Findings
{chr(10).join(f"- {f}" for f in pm.dependency_findings) if pm.dependency_findings else "- All dependency checks normal."}

## 4. Mitigation & Response
- **Recommended Action:** {pm.mitigation_recommendation or 'None'}
- **Commander Final Decision:** {pm.commander_decision}
- **Decision Rationale:** {pm.decision_justification}
- **Escalation Required:** {pm.escalation_status}

## 5. Stakeholder Communication
> {pm.status_page_message or 'No broadcast generated.'}
"""
        st.markdown(md_report)
        st.download_button(
            label="📥 Export Postmortem Markdown",
            data=md_report,
            file_name=f"postmortem_{pm.incident_id}.md",
            mime="text/markdown"
        )
        st.download_button(
            label="📥 Export Postmortem JSON",
            data=pm.model_dump_json(indent=2),
            file_name=f"postmortem_{pm.incident_id}.json",
            mime="application/json"
        )

# ----------------- SECTION H: Communication Panel -----------------
with tab_comm:
    st.subheader("Status Page & Stakeholder Broadcasts")
    
    if current_incident.status_updates:
        for upd in current_incident.status_updates:
            st.info(
                f"### {upd.headline}\n\n"
                f"{upd.message}\n\n"
                f"**Severity:** `{upd.severity.value}` | **Status:** `{upd.status.value}` | **Audience:** `{upd.audience}` | **Time:** `{upd.timestamp}`"
            )
    else:
        st.write("No stakeholder status broadcasts generated yet.")
