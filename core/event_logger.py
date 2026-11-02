"""
Append-Only Event Logger for AI IncidentOps.
Ensures an immutable, chronological, traceable record of all agent interactions.
"""

import json
import sqlite3
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from core.schemas import TimelineEvent


class EventLogger:
    """Thread-safe append-only event logger backed by SQLite."""

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._lock:
            with self._get_connection() as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS event_log (
                        seq INTEGER PRIMARY KEY AUTOINCREMENT,
                        event_id TEXT UNIQUE NOT NULL,
                        incident_id TEXT NOT NULL,
                        agent TEXT NOT NULL,
                        event_type TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        payload TEXT NOT NULL,
                        evidence_ids TEXT NOT NULL
                    )
                """)
                conn.execute("CREATE INDEX IF NOT EXISTS idx_events_incident ON event_log(incident_id)")
                conn.commit()

    def log_event(
        self,
        incident_id: str,
        agent: str,
        event_type: str,
        payload: Optional[Dict[str, Any]] = None,
        evidence_ids: Optional[List[str]] = None,
        timestamp: Optional[str] = None
    ) -> TimelineEvent:
        """Appends a new event immutably to the event log."""
        if not timestamp:
            timestamp = datetime.now(timezone.utc).isoformat()
        if payload is None:
            payload = {}
        if evidence_ids is None:
            evidence_ids = []

        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM event_log WHERE incident_id = ?", (incident_id,))
                count = cursor.fetchone()[0] + 1
                event_id = f"EVT-{incident_id[-4:] if len(incident_id) >= 4 else '0000'}-{count:03d}"
                
                event = TimelineEvent(
                    event_id=event_id,
                    incident_id=incident_id,
                    agent=agent,
                    event_type=event_type,
                    timestamp=timestamp,
                    payload=payload,
                    evidence_ids=evidence_ids
                )

                conn.execute(
                    """
                    INSERT INTO event_log (event_id, incident_id, agent, event_type, timestamp, payload, evidence_ids)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        event.event_id,
                        event.incident_id,
                        event.agent,
                        event.event_type,
                        event.timestamp,
                        json.dumps(event.payload),
                        json.dumps(event.evidence_ids)
                    )
                )
                conn.commit()
                return event

    def get_events(self, incident_id: str) -> List[TimelineEvent]:
        """Retrieves chronological events for a given incident."""
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT event_id, incident_id, agent, event_type, timestamp, payload, evidence_ids
                    FROM event_log
                    WHERE incident_id = ?
                    ORDER BY seq ASC
                    """,
                    (incident_id,)
                )
                rows = cursor.fetchall()
                events = []
                for row in rows:
                    events.append(
                        TimelineEvent(
                            event_id=row["event_id"],
                            incident_id=row["incident_id"],
                            agent=row["agent"],
                            event_type=row["event_type"],
                            timestamp=row["timestamp"],
                            payload=json.loads(row["payload"]),
                            evidence_ids=json.loads(row["evidence_ids"])
                        )
                    )
                return events

    def get_all_events(self) -> List[TimelineEvent]:
        """Retrieves all events across all incidents in chronological order."""
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT event_id, incident_id, agent, event_type, timestamp, payload, evidence_ids
                    FROM event_log
                    ORDER BY seq ASC
                    """
                )
                rows = cursor.fetchall()
                return [
                    TimelineEvent(
                        event_id=row["event_id"],
                        incident_id=row["incident_id"],
                        agent=row["agent"],
                        event_type=row["event_type"],
                        timestamp=row["timestamp"],
                        payload=json.loads(row["payload"]),
                        evidence_ids=json.loads(row["evidence_ids"])
                    )
                    for row in rows
                ]
