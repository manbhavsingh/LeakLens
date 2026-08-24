from __future__ import annotations

from dataclasses import asdict
from typing import Iterable

from .detector import detect_cohort_leaks
from .models import Transaction


def find_revenue_leaks(transactions: Iterable[Transaction]) -> list[dict]:
    """Return structured findings suitable for an AI investigator tool call."""
    return [asdict(candidate) for candidate in detect_cohort_leaks(transactions)]


def get_payment_failure_breakdown(
    transactions: Iterable[Transaction],
    *,
    payment_method: str | None = None,
) -> dict[str, int]:
    rows = list(transactions)
    if payment_method:
        rows = [r for r in rows if r.payment_method.value == payment_method]

    breakdown: dict[str, int] = {}
    for row in rows:
        if row.failure_reason:
            breakdown[row.failure_reason] = breakdown.get(row.failure_reason, 0) + 1
    return dict(sorted(breakdown.items(), key=lambda item: (-item[1], item[0])))
