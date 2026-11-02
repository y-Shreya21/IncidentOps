"""
Prometheus Metrics & Observability Instrumentation for AI IncidentOps (Layer 12).
Collects execution latencies, incident counters, and agent tool error rates.
"""

from __future__ import annotations

import time
from typing import Dict


class MetricsRegistry:
    """Thread-safe Prometheus-compatible metrics registry."""

    def __init__(self):
        self.incident_total: Dict[str, int] = {}
        self.agent_execution_seconds: Dict[str, float] = {}
        self.tool_execution_errors: Dict[str, int] = {}
        self.total_investigations: int = 0
        self.start_time: float = time.time()

    def inc_incident(self, severity: str, service: str):
        key = f'{severity}_{service}'
        self.incident_total[key] = self.incident_total.get(key, 0) + 1
        self.total_investigations += 1

    def observe_agent_time(self, agent: str, duration: float):
        self.agent_execution_seconds[agent] = duration

    def inc_tool_error(self, tool_name: str):
        self.tool_execution_errors[tool_name] = self.tool_execution_errors.get(tool_name, 0) + 1

    def generate_prometheus_text(self) -> str:
        """Emits standard Prometheus text format exposition."""
        lines = [
            "# HELP incidentops_uptime_seconds Total system uptime in seconds.",
            "# TYPE incidentops_uptime_seconds gauge",
            f"incidentops_uptime_seconds {time.time() - self.start_time:.1f}",
            "",
            "# HELP incidentops_investigations_total Total incident investigations executed.",
            "# TYPE incidentops_investigations_total counter",
            f"incidentops_investigations_total {self.total_investigations}",
            "",
            "# HELP incidentops_incidents_by_severity Incidents received grouped by severity.",
            "# TYPE incidentops_incidents_by_severity counter",
        ]
        for key, count in self.incident_total.items():
            sev, svc = key.split('_', 1) if '_' in key else (key, 'unknown')
            lines.append(f'incidentops_incidents_by_severity{{severity="{sev}",service="{svc}"}} {count}')

        lines.extend([
            "",
            "# HELP incidentops_agent_duration_seconds Last execution duration per agent.",
            "# TYPE incidentops_agent_duration_seconds gauge",
        ])
        for agent, dur in self.agent_execution_seconds.items():
            lines.append(f'incidentops_agent_duration_seconds{{agent="{agent}"}} {dur:.3f}')

        lines.extend([
            "",
            "# HELP incidentops_tool_errors_total Tool execution failure counters.",
            "# TYPE incidentops_tool_errors_total counter",
        ])
        for tool, errs in self.tool_execution_errors.items():
            lines.append(f'incidentops_tool_errors_total{{tool="{tool}"}} {errs}')

        return "\n".join(lines) + "\n"


metrics = MetricsRegistry()
