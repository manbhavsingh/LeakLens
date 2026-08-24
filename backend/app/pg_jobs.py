from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy import text
from sqlalchemy.orm import Session


CREATE_JOBS_SQL = """
CREATE TABLE IF NOT EXISTS investigation_jobs (
    id TEXT PRIMARY KEY,
    event_id TEXT NOT NULL UNIQUE,
    job_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    attempts INTEGER NOT NULL DEFAULT 0,
    max_attempts INTEGER NOT NULL DEFAULT 3,
    locked_at TIMESTAMPTZ,
    last_error TEXT,
    created_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ
)
"""


class PostgresJobRepository:
    def __init__(self, session: Session):
        self.session = session

    def create_table(self) -> None:
        self.session.execute(text(CREATE_JOBS_SQL))
        self.session.commit()

    def enqueue(self, job_id: str, event_id: str, job_type: str, max_attempts: int = 3) -> bool:
        result = self.session.execute(text("""
            INSERT INTO investigation_jobs
              (id, event_id, job_type, status, attempts, max_attempts, created_at)
            VALUES (:id, :event_id, :job_type, 'pending', 0, :max_attempts, :created_at)
            ON CONFLICT (event_id) DO NOTHING
        """), {
            "id": job_id, "event_id": event_id, "job_type": job_type,
            "max_attempts": max_attempts, "created_at": datetime.now(timezone.utc),
        })
        self.session.commit()
        return result.rowcount == 1

    def claim_one(self, lock_timeout_seconds: int = 300) -> dict | None:
        """Atomically claim one pending/recoverable job for this worker."""
        result = self.session.execute(text("""
            WITH candidate AS (
                SELECT id
                FROM investigation_jobs
                WHERE (
                    status = 'pending'
                    OR (status = 'running' AND locked_at < NOW() - (:timeout * INTERVAL '1 second'))
                )
                AND attempts < max_attempts
                ORDER BY created_at
                FOR UPDATE SKIP LOCKED
                LIMIT 1
            )
            UPDATE investigation_jobs j
            SET status = 'running', locked_at = NOW(), attempts = j.attempts + 1
            FROM candidate c
            WHERE j.id = c.id
            RETURNING j.id, j.event_id, j.job_type, j.attempts, j.max_attempts
        """), {"timeout": lock_timeout_seconds})
        row = result.mappings().first()
        self.session.commit()
        return dict(row) if row else None

    def succeed(self, job_id: str) -> None:
        self.session.execute(text("""
            UPDATE investigation_jobs
            SET status = 'succeeded', locked_at = NULL, completed_at = NOW(), last_error = NULL
            WHERE id = :id AND status = 'running'
        """), {"id": job_id})
        self.session.commit()

    def fail(self, job_id: str, error: str) -> None:
        self.session.execute(text("""
            UPDATE investigation_jobs
            SET status = CASE WHEN attempts >= max_attempts THEN 'failed' ELSE 'pending' END,
                locked_at = NULL,
                last_error = :error
            WHERE id = :id AND status = 'running'
        """), {"id": job_id, "error": error[:4000]})
        self.session.commit()
