"""
Logs Agent Tools.
Provides real log file retrieval and deterministic log pattern analysis.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Annotated, Any, Dict, List, Optional
from datetime import datetime, timezone
from semantic_kernel.functions import kernel_function

from core.config import settings


class LogTools:
    """Tools used by the Logs Agent."""

    def __init__(self, logs_dir: Optional[Path] = None):
        self.logs_dir = logs_dir or settings.LOGS_DIR

    @kernel_function(
        name="retrieve_recent_logs",
        description="Retrieves the most recent log lines from local service log files."
    )
    def retrieve_recent_logs(
        self,
        service_name: Annotated[str, "Name of the service whose logs to retrieve"],
        max_lines: Annotated[int, "Maximum number of recent lines to retrieve"] = 100
    ) -> Dict[str, Any]:
        """
        Reads actual log lines from the service log file on disk.
        """
        log_file = self.logs_dir / f"{service_name}.log"
        if not log_file.exists():
            # Check alternative naming
            candidates = list(self.logs_dir.glob(f"*{service_name}*.log"))
            if candidates:
                log_file = candidates[0]
            else:
                return {
                    "success": False,
                    "error": f"Log file for '{service_name}' not found at {log_file}",
                    "log_lines": [],
                    "total_lines": 0,
                    "source": str(log_file)
                }

        try:
            with open(log_file, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
            
            recent = [line.rstrip() for line in lines[-max_lines:]]
            return {
                "success": True,
                "error": None,
                "log_lines": recent,
                "total_lines": len(lines),
                "source": str(log_file)
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed reading log file: {str(e)}",
                "log_lines": [],
                "total_lines": 0,
                "source": str(log_file)
            }

    @kernel_function(
        name="analyze_log_patterns",
        description="Deterministically analyzes log lines to extract errors, patterns, and anomalies."
    )
    def analyze_log_patterns(
        self,
        log_lines: Annotated[List[str], "List of raw log lines to analyze"],
        service_name: Annotated[str, "Service name context"] = ""
    ) -> Dict[str, Any]:
        """
        Extracts errors, exceptions, repeated error messages, timestamps, and anomalous patterns.
        """
        if not log_lines:
            return {
                "has_errors": False,
                "error_count": 0,
                "error_patterns": [],
                "summary": "No logs provided for analysis",
                "primary_pattern": None,
                "timestamps": []
            }

        error_regexes = [
            (r"(?i)(psycopg2\.OperationalError|connection\s+refused|connection\s+timeout|database\s+unreachable|could\s+not\s+connect\s+to\s+server)", "database_connection_timeout"),
            (r"(?i)(deployment\s+failed|ModuleNotFoundError|ImportError|NullPointerException|AttributeError.*v2\.\d+|release.*regression)", "deployment_bug_crash"),
            (r"(?i)(cpu\s+usage\s*>\s*9\d%|thread\s+pool\s+exhausted|OutOfMemoryError|GC\s+overhead\s+limit|CPU\s+saturation)", "cpu_resource_exhaustion"),
            (r"(?i)(HTTP\s+5\d\d|Internal\s+Server\s+Error|502\s+Bad\s+Gateway|504\s+Gateway\s+Timeout)", "http_5xx_errors"),
            (r"(?i)(ERROR|CRITICAL|FATAL|Exception)", "generic_error")
        ]

        timestamp_regex = r"\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}"

        matched_patterns: Dict[str, List[str]] = {}
        all_errors: List[str] = []
        found_timestamps: List[str] = []

        for line in log_lines:
            ts_match = re.search(timestamp_regex, line)
            if ts_match:
                found_timestamps.append(ts_match.group(0))

            for pattern, pattern_name in error_regexes:
                if re.search(pattern, line):
                    if pattern_name not in matched_patterns:
                        matched_patterns[pattern_name] = []
                    matched_patterns[pattern_name].append(line)
                    all_errors.append(line)
                    break

        total_errors = len(all_errors)
        primary_pattern = None

        if "database_connection_timeout" in matched_patterns:
            primary_pattern = "database_connection_timeout"
        elif "deployment_bug_crash" in matched_patterns:
            primary_pattern = "deployment_bug_crash"
        elif "cpu_resource_exhaustion" in matched_patterns:
            primary_pattern = "cpu_resource_exhaustion"
        elif "http_5xx_errors" in matched_patterns:
            primary_pattern = "http_5xx_errors"
        elif "generic_error" in matched_patterns:
            primary_pattern = "generic_error"

        summary = (
            f"Detected {total_errors} error events across {len(log_lines)} lines. "
            f"Dominant pattern: {primary_pattern or 'None (normal logs)'}."
        )

        pattern_summary = [
            {
                "pattern_type": pat,
                "count": len(lines),
                "sample": lines[0] if lines else ""
            }
            for pat, lines in matched_patterns.items()
        ]

        return {
            "has_errors": total_errors > 0,
            "error_count": total_errors,
            "primary_pattern": primary_pattern,
            "error_patterns": pattern_summary,
            "summary": summary,
            "sample_errors": all_errors[:5],
            "timestamps": found_timestamps[-5:] if found_timestamps else []
        }


def retrieve_recent_logs(service_name: str, max_lines: int = 100, logs_dir: Optional[Path] = None) -> Dict[str, Any]:
    return LogTools(logs_dir).retrieve_recent_logs(service_name, max_lines)


def analyze_log_patterns(log_lines: List[str], service_name: str = "") -> Dict[str, Any]:
    return LogTools().analyze_log_patterns(log_lines, service_name)
