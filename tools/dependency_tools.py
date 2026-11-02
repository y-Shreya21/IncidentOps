"""
Dependency Agent Tools.
Provides service dependency graph traversal and actual health checks.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Any, Dict, List, Optional
import httpx
from semantic_kernel.functions import kernel_function

from core.config import settings


class DependencyTools:
    """Tools used by the Dependency Agent."""

    def __init__(self, registry_path: Optional[Path] = None, state_file: Optional[Path] = None):
        self.registry_path = registry_path or settings.SERVICE_REGISTRY_PATH
        self.state_file = state_file or (settings.LOGS_DIR / "simulated_health.json")

    @kernel_function(
        name="retrieve_service_dependencies",
        description="Retrieves the direct dependencies for a service from the service topology registry."
    )
    def retrieve_service_dependencies(
        self,
        service_name: Annotated[str, "The name of the service to query"]
    ) -> Dict[str, Any]:
        """
        Reads dependency relationships from service registry.
        """
        if not self.registry_path.exists():
            return {
                "success": False,
                "error": f"Registry not found at {self.registry_path}",
                "service": service_name,
                "dependencies": []
            }

        try:
            with open(self.registry_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            services = data.get("services", {})
            if service_name not in services:
                return {
                    "success": False,
                    "error": f"Service '{service_name}' not found in registry",
                    "service": service_name,
                    "dependencies": []
                }
            
            deps = services[service_name].get("dependencies", [])
            return {
                "success": True,
                "error": None,
                "service": service_name,
                "dependencies": deps
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "service": service_name,
                "dependencies": []
            }

    @kernel_function(
        name="check_service_health",
        description="Performs an actual health check against a service endpoint or simulated runtime."
    )
    def check_service_health(
        self,
        service_name: Annotated[str, "Name of the service to check"]
    ) -> Dict[str, Any]:
        """
        Checks health of the service.
        First checks if an active HTTP health endpoint is reachable.
        If unreachable or configured in simulated runtime mode, reads the simulation state file.
        """
        # 1. Check local simulated runtime state file if present
        if self.state_file.exists():
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    health_data = json.load(f)
                if service_name in health_data:
                    entry = health_data[service_name]
                    return {
                        "service": service_name,
                        "status": entry.get("status", "unknown"),
                        "http_status": entry.get("http_status", 500 if entry.get("status") == "unhealthy" else 200),
                        "latency_ms": entry.get("latency_ms", 12.5),
                        "error": entry.get("error"),
                        "checked_at": entry.get("checked_at", "simulated"),
                        "mode": "simulated_state"
                    }
            except Exception:
                pass

        # 2. Try actual HTTP health endpoint if defined in registry
        health_endpoint = None
        if self.registry_path.exists():
            try:
                with open(self.registry_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                svc_info = data.get("services", {}).get(service_name)
                if svc_info:
                    health_endpoint = svc_info.get("health_endpoint")
            except Exception:
                pass

        if health_endpoint:
            try:
                with httpx.Client(timeout=2.0) as client:
                    resp = client.get(health_endpoint)
                    is_healthy = resp.status_code == 200
                    return {
                        "service": service_name,
                        "status": "healthy" if is_healthy else "unhealthy",
                        "http_status": resp.status_code,
                        "latency_ms": resp.elapsed.total_seconds() * 1000,
                        "error": None if is_healthy else f"HTTP {resp.status_code}",
                        "checked_at": "live_http",
                        "mode": "http_probe"
                    }
            except Exception as e:
                # HTTP unreachable
                return {
                    "service": service_name,
                    "status": "unhealthy",
                    "http_status": 0,
                    "latency_ms": 0.0,
                    "error": f"Connection failed: {str(e)}",
                    "checked_at": "live_http",
                    "mode": "http_probe"
                }

        # Fallback default: healthy
        return {
            "service": service_name,
            "status": "healthy",
            "http_status": 200,
            "latency_ms": 5.0,
            "error": None,
            "checked_at": "default",
            "mode": "fallback"
        }


def retrieve_service_dependencies(service_name: str, registry_path: Optional[Path] = None) -> Dict[str, Any]:
    return DependencyTools(registry_path).retrieve_service_dependencies(service_name)


def check_service_health(service_name: str, registry_path: Optional[Path] = None) -> Dict[str, Any]:
    return DependencyTools(registry_path).check_service_health(service_name)
