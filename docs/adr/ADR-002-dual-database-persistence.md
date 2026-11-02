# ADR-002: Dual Database Persistence Strategy (PostgreSQL & SQLite)

## Status
Accepted

## Context
Enterprise operations environments utilize robust relational databases (PostgreSQL) with clustering, replication, and connection pooling. However, academic demonstrations, local development, automated CI pipelines, and pytest suites require fast, lightweight, zero-dependency persistence without requiring external Docker services to be pre-running.

## Decision
We implement a dual-storage design:
1. **SQLite Default**: Out-of-the-box local development, testing, and Jupyter notebook execution store data in `database/incidentops.db`.
2. **PostgreSQL Production Target**: Containerized and cloud deployments connect via SQLAlchemy ORM and Alembic migrations when `DATABASE_URL=postgresql://...` is configured.

## Consequences
- Pytest and scenario suites run in under 1 second without external infrastructure dependencies.
- Enterprise deployments in Docker/ECS seamlessly point to managed PostgreSQL instances.
