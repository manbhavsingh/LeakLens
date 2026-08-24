from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from typing import Iterable

from .models import Transaction, TransactionStatus


def compare_time_windows(
    transactions: Iterable[Transaction],
    *,
    start: datetime,
    split: datetime,
    end: datetime,
) -> dict[str, float | int]:
    rows = list(transactions)
    before = [r for r in rows if start <= r.occurred_at < split]
    after = [r for r in rows if split <= r.occurred_at < end]

    def conversion(items: list[Transaction]) -> float:
        return (
            sum(r.status is TransactionStatus.SUCCESS for r in items) / len(items)
            if items else 0.0
        )

    return {
        "before_transactions": len(before),
        "after_transactions": len(after),
        "before_conversion": conversion(before),
        "after_conversion": conversion(after),
        "conversion_change": conversion(after) - conversion(before),
    }


def get_customer_history(
    transactions: Iterable[Transaction],
    customer_id: str,
) -> dict[str, object]:
    rows = [r for r in transactions if r.customer_id == customer_id]
    successful = [r for r in rows if r.status is TransactionStatus.SUCCESS]
    total_value = sum((r.amount for r in successful), Decimal("0"))
    return {
        "customer_id": customer_id,
        "transaction_count": len(rows),
        "successful_transactions": len(successful),
        "success_rate": len(successful) / len(rows) if rows else 0.0,
        "lifetime_success_value": str(total_value),
        "last_transaction_at": max((r.occurred_at for r in rows), default=None),
    }


def calculate_revenue_impact(
    transactions: Iterable[Transaction],
    *,
    expected_conversion: float,
) -> dict[str, str | float | int]:
    rows = list(transactions)
    if not rows:
        return {"transactions": 0, "expected_successes": 0, "actual_successes": 0, "revenue_at_risk": "0.00"}

    actual_successes = sum(r.status is TransactionStatus.SUCCESS for r in rows)
    expected_successes = round(len(rows) * expected_conversion)
    missing = max(0, expected_successes - actual_successes)
    avg_amount = sum((r.amount for r in rows), Decimal("0")) / len(rows)
    risk = avg_amount * missing
    return {
        "transactions": len(rows),
        "expected_successes": expected_successes,
        "actual_successes": actual_successes,
        "revenue_at_risk": str(risk.quantize(Decimal("0.01"))),
    }
