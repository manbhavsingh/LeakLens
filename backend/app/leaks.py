from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Iterable

from .models import DeviceType, PaymentMethod, Transaction, TransactionStatus


@dataclass(frozen=True)
class InjectedLeak:
    name: str
    description: str
    affected_transaction_ids: tuple[str, ...]
    baseline_conversion: float
    leaked_conversion: float
    revenue_at_risk: Decimal


def inject_upi_android_evening_degradation(
    transactions: Iterable[Transaction],
    start_hour: int = 20,
    end_hour: int = 23,
    target_conversion: float = 0.52,
    seed: int = 42,
) -> InjectedLeak:
    """Inject a known UPI+Android evening conversion leak.

    Only transaction outcomes are changed. The leak metadata is returned as
    ground truth for evaluation and is intentionally not stored on transactions.
    """
    rows = [
        row for row in transactions
        if row.payment_method is PaymentMethod.UPI
        and row.device is DeviceType.ANDROID
        and start_hour <= row.occurred_at.hour < end_hour
    ]

    if not rows:
        return InjectedLeak(
            name="upi_android_evening_degradation",
            description="No matching cohort in generated data.",
            affected_transaction_ids=(),
            baseline_conversion=0.0,
            leaked_conversion=0.0,
            revenue_at_risk=Decimal("0"),
        )

    successful = [row for row in rows if row.status is TransactionStatus.SUCCESS]
    baseline = len(successful) / len(rows)
    target_successes = round(len(rows) * target_conversion)

    # Deterministic selection keeps evaluation reproducible across runs.
    ranked = sorted(rows, key=lambda row: row.event_id)
    for row in ranked:
        row.status = TransactionStatus.SUCCESS
        row.failure_reason = None

    for row in ranked[target_successes:]:
        row.status = TransactionStatus.FAILED
        row.failure_reason = "timeout"

    lost = sum((row.amount for row in ranked[target_successes:] if row.amount), Decimal("0"))

    return InjectedLeak(
        name="upi_android_evening_degradation",
        description="UPI conversion degradation for Android users from 20:00 to 23:00.",
        affected_transaction_ids=tuple(row.event_id for row in ranked),
        baseline_conversion=baseline,
        leaked_conversion=target_conversion,
        revenue_at_risk=lost,
    )
