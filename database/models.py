"""
SQLAlchemy ORM Data Models for AI IncidentOps.
Supports both PostgreSQL and SQLite backends with complete relational integrity.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Text,
    Integer,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    role = Column(String(32), nullable=False, default="IncidentResponder")  # Administrator, IncidentResponder, SREEngineer, Stakeholder
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ServiceModel(Base):
    __tablename__ = "services"

    name = Column(String(64), primary_key=True)
    tier = Column(String(32), default="tier-1")
    owner = Column(String(64), default="platform-engineering")
    health_endpoint = Column(String(256), default="/health")
    metrics_endpoint = Column(String(256), default="/metrics")
    logs_path = Column(String(256), default="logs/service.log")


class ServiceDependencyModel(Base):
    __tablename__ = "service_dependencies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    service_name = Column(String(64), ForeignKey("services.name"), nullable=False, index=True)
    dependency_name = Column(String(64), nullable=False)


class IncidentModel(Base):
    __tablename__ = "incidents"

    incident_id = Column(String(32), primary_key=True, index=True)
    service = Column(String(64), nullable=False, index=True)
    symptom = Column(Text, nullable=False)
    severity = Column(String(16), nullable=False)
    status = Column(String(32), nullable=False, default="investigating")
    created_at = Column(String(64), nullable=False)
    description = Column(Text, nullable=False)
    escalation_status = Column(String(32), default="none")


class EvidenceModel(Base):
    __tablename__ = "evidence"

    evidence_id = Column(String(32), primary_key=True)
    incident_id = Column(String(32), ForeignKey("incidents.incident_id"), primary_key=True, index=True)
    agent = Column(String(64), nullable=False)
    finding = Column(Text, nullable=False)
    service = Column(String(64), nullable=False)
    evidence_source = Column(String(256), nullable=False)
    evidence_timestamp = Column(String(64), nullable=False)
    raw_data = Column(Text, nullable=False)  # JSON-encoded dictionary


class MitigationProposalModel(Base):
    __tablename__ = "mitigation_proposals"

    proposal_id = Column(String(32), primary_key=True)
    incident_id = Column(String(32), ForeignKey("incidents.incident_id"), primary_key=True, index=True)
    agent = Column(String(64), nullable=False)
    proposed_action = Column(String(64), nullable=False)
    target_service = Column(String(64), nullable=False)
    reason = Column(Text, nullable=False)
    supporting_evidence = Column(Text, nullable=False)  # JSON-encoded list of IDs
    risk_level = Column(String(16), default="medium")


class DecisionModel(Base):
    __tablename__ = "decisions"

    incident_id = Column(String(32), ForeignKey("incidents.incident_id"), primary_key=True)
    likely_root_cause = Column(Text, nullable=False)
    root_cause_evidence = Column(Text, nullable=False)  # JSON-encoded list of IDs
    mitigation_decision = Column(String(64), nullable=False)
    target_service = Column(String(64), nullable=False)
    decision_reason = Column(Text, nullable=False)
    decision_status = Column(String(32), nullable=False)
    incident_status = Column(String(32), nullable=False)
    confidence = Column(Float, nullable=False)
    escalation_required = Column(Integer, default=0)
    timestamp = Column(String(64), nullable=False)


class EventLogModel(Base):
    __tablename__ = "event_log"

    seq = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(32), unique=True, nullable=False, index=True)
    incident_id = Column(String(32), nullable=False, index=True)
    agent = Column(String(64), nullable=False)
    event_type = Column(String(64), nullable=False)
    timestamp = Column(String(64), nullable=False)
    payload = Column(Text, nullable=False)  # JSON-encoded dict
    evidence_ids = Column(Text, nullable=False)  # JSON-encoded list


class StatusUpdateModel(Base):
    __tablename__ = "status_updates"

    update_id = Column(String(32), primary_key=True)
    incident_id = Column(String(32), ForeignKey("incidents.incident_id"), primary_key=True, index=True)
    severity = Column(String(16), nullable=False)
    status = Column(String(32), nullable=False)
    timestamp = Column(String(64), nullable=False)
    headline = Column(Text, nullable=False)
    message = Column(Text, nullable=False)
    audience = Column(String(32), default="public")
