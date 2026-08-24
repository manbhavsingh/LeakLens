from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable

from .models import Transaction, TransactionStatus


@dataclass(frozen=True)
class CohortMetrics:
    transactions: int
    successful_transactions: int
    conversion_rate: float
    gross_revenue: Decimal
    failed_revenue: Decimal


def calculate_metrics(transactions: Iterable[Transaction]) -> CohortMetrics:
    rows = list(transactions)
    total = len(rows)
    successful = sum(row.status is TransactionStatus.SUCCESS for row in rows)
    gross_revenue = sum(
        (row.amount for row in rows if row.status is TransactionStatus.SUCCESS),
        Decimal("0"),
    )
    failed_revenue = sum(
        (row.amount for row in rows if row.status is not TransactionStatus.SUCCESS),
        Decimal("0"),
    )
    return CohortMetrics(
        transactions=total,
        successful_transactions=successful,
        conversion_rate=successful / total if total else 0.0,
        gross_revenue=gross_revenue,
        failed_revenue=failed_revenue,
    )
