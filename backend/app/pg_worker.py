from __future__ import annotations

import logging
import time
from collections.abc import Callable

from .pg_jobs import PostgresJobRepository

logger = logging.getLogger(__name__)


class PostgresWorker:
    def __init__(self, repository: PostgresJobRepository, handler: Callable[[dict], None]):
        self.repository = repository
        self.handler = handler

    def process_once(self) -> bool:
        job = self.repository.claim_one()
        if not job:
            return False
        try:
            self.handler(job)
        except Exception as exc:
            logger.exception("job %s failed", job["id"])
            self.repository.fail(job["id"], str(exc))
        else:
            self.repository.succeed(job["id"])
        return True

    def run_forever(self, poll_interval: float = 1.0) -> None:
        while True:
            if not self.process_once():
                time.sleep(poll_interval)
