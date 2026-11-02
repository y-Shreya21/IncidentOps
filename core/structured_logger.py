"""
Structured JSON Logging Module for AI IncidentOps (Layer 11).
Formats application, agent, and tool logs into machine-parsable JSON.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional


class JSONFormatter(logging.Formatter):
    """Custom logging formatter outputting single-line structured JSON."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Contextual metadata if attached
        if hasattr(record, "incident_id"):
            log_obj["incident_id"] = getattr(record, "incident_id")
        if hasattr(record, "agent"):
            log_obj["agent"] = getattr(record, "agent")
        if hasattr(record, "tool"):
            log_obj["tool"] = getattr(record, "tool")
        if hasattr(record, "duration_ms"):
            log_obj["duration_ms"] = getattr(record, "duration_ms")
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_obj)


def setup_structured_logging(level: int = logging.INFO):
    """Configures root logger with JSON formatting."""
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    # Clear existing handlers
    root_logger.handlers = [handler]
    return root_logger
