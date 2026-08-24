from __future__ import annotations

from fastapi import APIRouter

from .observability import metrics

router = APIRouter()


@router.get("/ready")
def ready() -> dict[str, str]:
    return {"status": "ready"}


@router.get("/metrics")
def metrics_snapshot() -> dict[str, int]:
    return metrics.snapshot()
