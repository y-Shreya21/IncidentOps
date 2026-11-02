# Multi-stage Dockerfile for AI IncidentOps (Backend + React Dashboard)

# Stage 1: Build React Frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Python Backend Runtime
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

# Copy built frontend distribution so FastAPI serves React UI directly at root /
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Expose default port
ENV PORT=8000
EXPOSE 8000

# Health check
HEALTHCHECK --interval=10s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/api/v1/health || exit 1

# Run FastAPI backend with dynamic port support (Render, Railway, GCP, AWS)
CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
