"""
Generic simulated microservice for Docker Compose testing.
Supports dynamic failure injection via /fail and /recover endpoints.
"""

import os
import sys
import logging
from fastapi import FastAPI, HTTPException
import uvicorn

service_name = os.getenv("SERVICE_NAME", "simulated-service")
port = int(os.getenv("PORT", 8080))

app = FastAPI(title=service_name)
is_healthy = True
failure_reason = ""

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(service_name)


@app.get("/health")
def health():
    if not is_healthy:
        logger.error(f"Health check failed: {failure_reason}")
        raise HTTPException(status_code=500, detail=failure_reason)
    return {"status": "healthy", "service": service_name}


@app.get("/metrics")
def metrics():
    return {
        "service": service_name,
        "uptime_seconds": 3600,
        "requests_total": 15420,
        "error_rate": 0.0 if is_healthy else 0.85
    }


@app.post("/fail")
def inject_failure(reason: str = "Injected simulated outage"):
    global is_healthy, failure_reason
    is_healthy = False
    failure_reason = reason
    logger.error(f"Failure injected: {reason}")
    return {"status": "failed", "reason": reason}


@app.post("/recover")
def recover():
    global is_healthy, failure_reason
    is_healthy = True
    failure_reason = ""
    logger.info("Service recovered to healthy status")
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=port)
