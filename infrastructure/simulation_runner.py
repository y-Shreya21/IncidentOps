"""
Simulation Runner for AI IncidentOps.
Sets up reproducible local incident scenarios generating real log files
and service health states for end-to-end multi-agent execution and testing.
"""

from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Any, Dict

from core.config import settings


class SimulationRunner:
    """Manages failure scenario injection and log file generation."""

    def __init__(self, logs_dir: Path = settings.LOGS_DIR):
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.health_file = self.logs_dir / "simulated_health.json"

    def reset(self) -> None:
        """Resets all logs and marks all services healthy."""
        healthy_state = {
            "frontend": {"status": "healthy", "http_status": 200, "latency_ms": 12.0, "error": None},
            "payment-api": {"status": "healthy", "http_status": 200, "latency_ms": 18.0, "error": None},
            "auth-service": {"status": "healthy", "http_status": 200, "latency_ms": 15.0, "error": None},
            "postgres": {"status": "healthy", "http_status": 200, "latency_ms": 4.5, "error": None}
        }
        with open(self.health_file, "w", encoding="utf-8") as f:
            json.dump(healthy_state, f, indent=2)

        for svc in ["frontend", "payment-api", "auth-service", "postgres"]:
            log_file = self.logs_dir / f"{svc}.log"
            now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            with open(log_file, "w", encoding="utf-8") as f:
                f.write(f"{now} [INFO] {svc} initialized in production environment.\n")
                f.write(f"{now} [INFO] Health probe check passed: 200 OK.\n")

    def setup_database_failure(self) -> Dict[str, Any]:
        """
        Scenario A: Database connectivity failure.
        Postgres is down. Payment API encounters repeated connection timeouts.
        """
        now = datetime.now(timezone.utc)
        ts_str = now.isoformat()

        # Update health states
        health_state = {
            "frontend": {"status": "healthy", "http_status": 200, "latency_ms": 25.0, "error": None},
            "payment-api": {"status": "unhealthy", "http_status": 500, "latency_ms": 2500.0, "error": "Database connection timeout"},
            "auth-service": {"status": "healthy", "http_status": 200, "latency_ms": 16.0, "error": None},
            "postgres": {"status": "unhealthy", "http_status": 503, "latency_ms": 0.0, "error": "Connection refused (port 5432)"}
        }
        with open(self.health_file, "w", encoding="utf-8") as f:
            json.dump(health_state, f, indent=2)

        # Generate realistic payment-api log
        log_file = self.logs_dir / "payment-api.log"
        with open(log_file, "w", encoding="utf-8") as f:
            for i in range(10):
                t = (now - timedelta(seconds=120 - i * 10)).strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"{t} [INFO] POST /v1/checkout/process received transaction txn_{1000+i}\n")
            
            # Failure cascade
            for i in range(6):
                t = (now - timedelta(seconds=40 - i * 6)).strftime("%Y-%m-%d %H:%M:%S")
                f.write(
                    f"{t} [ERROR] Database connection timeout: could not connect to server postgres:5432 - "
                    f"psycopg2.OperationalError: Connection refused. Remaining pool: 0/20.\n"
                )
                f.write(f"{t} [CRITICAL] HTTP 500 Internal Server Error returned to checkout frontend.\n")

        return {
            "service": "payment-api",
            "symptom": "HTTP 500 errors and database connection timeout",
            "severity": "critical",
            "timestamp": ts_str,
            "description": "Payment API checkout requests failing with HTTP 500. Database pool exhausted."
        }

    def setup_deployment_failure(self) -> Dict[str, Any]:
        """
        Scenario B: Failed deployment.
        Payment API was updated to v2.4.1 which has a bug in checkout handler.
        Underlying infrastructure and database are healthy.
        """
        now = datetime.now(timezone.utc)
        ts_str = now.isoformat()

        # Health state: services are reachable, but payment-api returns 500 due to code crash
        health_state = {
            "frontend": {"status": "healthy", "http_status": 200, "latency_ms": 18.0, "error": None},
            "payment-api": {"status": "unhealthy", "http_status": 500, "latency_ms": 45.0, "error": "Internal application crash"},
            "auth-service": {"status": "healthy", "http_status": 200, "latency_ms": 14.0, "error": None},
            "postgres": {"status": "healthy", "http_status": 200, "latency_ms": 5.0, "error": None}
        }
        with open(self.health_file, "w", encoding="utf-8") as f:
            json.dump(health_state, f, indent=2)

        # Generate realistic payment-api log
        log_file = self.logs_dir / "payment-api.log"
        with open(log_file, "w", encoding="utf-8") as f:
            deploy_t = (now - timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"{deploy_t} [INFO] Initiating deployment of release v2.4.1 commit #7f2e1c\n")
            f.write(f"{deploy_t} [INFO] Application container reloaded with image payment-api:v2.4.1\n")
            
            for i in range(7):
                t = (now - timedelta(minutes=8 - i)).strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"{t} [ERROR] deployment failed: release regression in payment_gateway.py:142\n")
                f.write(f"{t} [ERROR] AttributeError: 'NoneType' object has no attribute 'customer_token' in v2.4.1\n")
                f.write(f"{t} [CRITICAL] HTTP 500 Internal Server Error returned on /v1/checkout/process\n")

        return {
            "service": "payment-api",
            "symptom": "Post-release 500 errors after deployment v2.4.1",
            "severity": "high",
            "timestamp": ts_str,
            "description": "Immediate spike in 500 errors on payment-api following release v2.4.1 deployment."
        }

    def setup_high_cpu(self) -> Dict[str, Any]:
        """
        Scenario C: High CPU utilization.
        Worker threads saturated, heavy latency and timeouts.
        """
        now = datetime.now(timezone.utc)
        ts_str = now.isoformat()

        health_state = {
            "frontend": {"status": "healthy", "http_status": 200, "latency_ms": 320.0, "error": None},
            "payment-api": {"status": "unhealthy", "http_status": 504, "latency_ms": 4500.0, "error": "Gateway Timeout / CPU 98%"},
            "auth-service": {"status": "healthy", "http_status": 200, "latency_ms": 15.0, "error": None},
            "postgres": {"status": "healthy", "http_status": 200, "latency_ms": 6.0, "error": None}
        }
        with open(self.health_file, "w", encoding="utf-8") as f:
            json.dump(health_state, f, indent=2)

        log_file = self.logs_dir / "payment-api.log"
        with open(log_file, "w", encoding="utf-8") as f:
            for i in range(5):
                t = (now - timedelta(seconds=60 - i * 10)).strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"{t} [WARNING] cpu usage > 96% on worker node pod-payment-7a8b.\n")
                f.write(f"{t} [ERROR] thread pool exhausted: CPU saturation active_threads=64/64 queue_depth=280\n")
                f.write(f"{t} [ERROR] HTTP 504 Gateway Timeout: upstream worker did not respond in 4000ms\n")

        return {
            "service": "payment-api",
            "symptom": "High CPU utilization and request queuing",
            "severity": "high",
            "timestamp": ts_str,
            "description": "Payment API CPU sustained at 98%, request queuing and worker thread exhaustion."
        }

    def setup_insufficient_evidence(self) -> Dict[str, Any]:
        """
        Scenario D: Insufficient Evidence.
        Vague report of error, but logs are completely normal and all services are healthy.
        The Incident Commander must NOT invent a root cause and must escalate safely.
        """
        now = datetime.now(timezone.utc)
        ts_str = now.isoformat()

        health_state = {
            "frontend": {"status": "healthy", "http_status": 200, "latency_ms": 12.0, "error": None},
            "payment-api": {"status": "healthy", "http_status": 200, "latency_ms": 15.0, "error": None},
            "auth-service": {"status": "healthy", "http_status": 200, "latency_ms": 11.0, "error": None},
            "postgres": {"status": "healthy", "http_status": 200, "latency_ms": 4.0, "error": None}
        }
        with open(self.health_file, "w", encoding="utf-8") as f:
            json.dump(health_state, f, indent=2)

        log_file = self.logs_dir / "payment-api.log"
        with open(log_file, "w", encoding="utf-8") as f:
            for i in range(12):
                t = (now - timedelta(seconds=120 - i * 10)).strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"{t} [INFO] GET /health returned 200 OK. Latency 14ms.\n")
                f.write(f"{t} [INFO] POST /v1/checkout/process completed successfully. HTTP 200 OK.\n")

        return {
            "service": "payment-api",
            "symptom": "Transient blip reported by customer",
            "severity": "medium",
            "timestamp": ts_str,
            "description": "Customer reported occasional slowness. Telemetry and logs appear normal."
        }


simulation = SimulationRunner()
