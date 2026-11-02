"""
FastAPI Backend for AI IncidentOps.
Exposes endpoints for alert ingestion, blackboard inspection,
simulation scenario triggers, RBAC authentication, and Prometheus metrics.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Query, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from core.config import settings
from core.incident_board import IncidentBoard
from core.orchestrator import IncidentOrchestrator
from core.schemas import AlertPayload, IncidentState, PostmortemReport, TimelineEvent
from core.metrics import metrics
from infrastructure.simulation_runner import simulation
from api.routes import auth, incidents

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("ai_incidentops.api")

app = FastAPI(
    title="AI IncidentOps API",
    version=settings.VERSION,
    description="Autonomous Multi-Agent IT Incident Response War-Room Backend API"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount modular routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(incidents.router, prefix="/api/v1")

# Shared board and orchestrator instances
board = IncidentBoard(settings.DB_PATH)
orchestrator = IncidentOrchestrator(board)


@app.get("/api/v1/health", tags=["System"])
def health_check():
    return {
        "status": "healthy",
        "service": "AI IncidentOps API",
        "version": settings.VERSION,
        "database": str(settings.DB_PATH),
    }


@app.get("/metrics", tags=["Observability"])
def get_metrics():
    """Prometheus metrics endpoint."""
    return Response(content=metrics.generate_prometheus_text(), media_type="text/plain")


@app.post("/api/v1/incidents/alert", response_model=PostmortemReport, tags=["Incidents"])
async def ingest_alert(alert: AlertPayload):
    """
    Ingests an incoming alert and triggers the autonomous multi-agent war-room response cycle.
    """
    try:
        metrics.inc_incident(alert.severity.value, alert.service)
        postmortem = await orchestrator.run_incident_response(alert.model_dump())
        return postmortem
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.exception("Failed during incident response orchestration")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.post("/api/v1/simulate/{scenario_name}", tags=["Simulation"])
async def run_simulation(scenario_name: str, auto_respond: bool = Query(True)):
    """
    Sets up a practical incident scenario and optionally runs the war-room response.
    Available scenarios: db_failure, deployment_failure, high_cpu, insufficient_evidence.
    """
    scenario_map = {
        "db_failure": simulation.setup_database_failure,
        "database_failure": simulation.setup_database_failure,
        "deployment_failure": simulation.setup_deployment_failure,
        "high_cpu": simulation.setup_high_cpu,
        "insufficient_evidence": simulation.setup_insufficient_evidence,
    }

    if scenario_name not in scenario_map:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown scenario '{scenario_name}'. Valid: {list(scenario_map.keys())}"
        )

    alert_dict = scenario_map[scenario_name]()
    
    if auto_respond:
        metrics.inc_incident(alert_dict.get("severity", "high"), alert_dict.get("service", "unknown"))
        postmortem = await orchestrator.run_incident_response(alert_dict)
        return {
            "scenario": scenario_name,
            "alert": alert_dict,
            "postmortem": postmortem
        }

    return {
        "scenario": scenario_name,
        "alert": alert_dict,
        "message": "Scenario environment initialized. Ingest alert to trigger war-room."
    }


@app.get("/api/v1/services", tags=["Services"])
def list_services():
    """Lists all registered services and their dependency relationships."""
    from tools.alert_tools import AlertTools
    import json
    
    tools = AlertTools()
    if tools.registry_path.exists():
        with open(tools.registry_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("services", {})
    return {}


# Mount built React frontend if distribution exists
dist_dir = settings.BASE_DIR / "frontend" / "dist"
if dist_dir.exists():
    app.mount("/", StaticFiles(directory=str(dist_dir), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
