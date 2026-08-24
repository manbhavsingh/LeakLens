from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from typing import Callable
from uuid import uuid4


class JobStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


@dataclass
class Job:
    id: str
    event_id: str
    job_type: str
    status: JobStatus = JobStatus.PENDING
    attempts: int = 0
    max_attempts: int = 3
    last_error: str | None = None
    created_at: datetime = datetime.now(timezone.utc)
    completed_at: datetime | None = None


class JobQueue:
    """Deterministic queue abstraction; storage can be backed by PostgreSQL."""

    def __init__(self) -> None:
        self.jobs: dict[str, Job] = {}
        self.event_to_job: dict[str, str] = {}

    def enqueue(self, *, event_id: str, job_type: str) -> Job:
        existing_id = self.event_to_job.get(event_id)
        if existing_id:
            return self.jobs[existing_id]
        job = Job(id=str(uuid4()), event_id=event_id, job_type=job_type)
        self.jobs[job.id] = job
        self.event_to_job[event_id] = job.id
        return job

    def run(self, job_id: str, handler: Callable[[Job], None]) -> Job:
        job = self.jobs[job_id]
        if job.status is JobStatus.SUCCEEDED:
            return job
        if job.attempts >= job.max_attempts:
            job.status = JobStatus.FAILED
            return job

        job.status = JobStatus.RUNNING
        job.attempts += 1
        try:
            handler(job)
            job.status = JobStatus.SUCCEEDED
            job.completed_at = datetime.now(timezone.utc)
            job.last_error = None
        except Exception as exc:
            job.status = JobStatus.FAILED if job.attempts >= job.max_attempts else JobStatus.PENDING
            job.last_error = str(exc)
        return job
