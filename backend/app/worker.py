from __future__ import annotations

import logging
import time
from collections.abc import Callable

from .jobs import Job, JobQueue, JobStatus

logger = logging.getLogger(__name__)


class InvestigationWorker:
    def __init__(self, queue: JobQueue, handler: Callable[[Job], None]):
        self.queue = queue
        self.handler = handler

    def process_once(self) -> Job | None:
        pending = next((job for job in self.queue.jobs.values() if job.status is JobStatus.PENDING), None)
        if pending is None:
            return None
        job = self.queue.run(pending.id, self.handler)
        if job.status is JobStatus.FAILED:
            logger.error("job failed permanently: %s", job.id)
        return job

    def run_until_empty(self, *, poll_interval: float = 0.0, max_cycles: int = 100) -> int:
        processed = 0
        for _ in range(max_cycles):
            job = self.process_once()
            if job is None:
                break
            processed += 1
            if poll_interval:
                time.sleep(poll_interval)
        return processed
