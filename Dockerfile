# Multi-stage Dockerfile for AI IncidentOps Backend
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application source
COPY agents/ ./agents/
COPY api/ ./api/
COPY core/ ./core/
COPY database/ ./database/
COPY infrastructure/ ./infrastructure/
COPY security/ ./security/
COPY tools/ ./tools/
COPY logs/ ./logs/
COPY pytest.ini .

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=10s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Run FastAPI backend with uvicorn
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
