from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from .jobs import JobQueue
from .pg_jobs import PostgresJobRepository


@dataclass(frozen=True)
class InvestigationOutcome:
    event_id: str
    status: str
    result: dict[str, Any]


class InvestigationPipeline:
    """Application boundary between durable events/jobs and investigation logic."""

    def __init__(self, investigator: Callable[[dict[str, Any]], dict[str, Any]]):
        self.investigator = investigator

    def handle(self, job: dict[str, Any], event: dict[str, Any]) -> InvestigationOutcome:
        result = self.investigator(event)
        return InvestigationOutcome(
            event_id=job["event_id"],
            status="completed",
            result=result,
        )


def enqueue_postgres_job(repository: PostgresJobRepository, event_id: str, job_id: str) -> bool:
    return repository.enqueue(
        job_id=job_id,
        event_id=event_id,
        job_type="investigate_payment_event",
    )


def enqueue_memory_job(queue: JobQueue, event_id: str):
    return queue.enqueue(event_id=event_id, job_type="investigate_payment_event")
