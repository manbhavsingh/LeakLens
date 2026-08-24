from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from dataclasses import dataclass

logger = logging.getLogger("leaklens")


@dataclass
class Metrics:
    webhook_events: int = 0
    duplicate_events: int = 0
    jobs_succeeded: int = 0
    jobs_failed: int = 0
    investigations: int = 0
    interventions_allowed: int = 0
    interventions_blocked: int = 0

    def snapshot(self) -> dict[str, int]:
        return self.__dict__.copy()


metrics = Metrics()


@contextmanager
def timed_operation(name: str):
    started = time.perf_counter()
    try:
        yield
    finally:
        logger.info("operation=%s duration_ms=%.2f", name, (time.perf_counter() - started) * 1000)
