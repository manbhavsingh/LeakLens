from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal
from itertools import product
from typing import Iterable

from .models import DeviceType, PaymentMethod, Transaction, TransactionStatus


@dataclass(frozen=True)
class LeakCandidate:
    title: str
    cohort: dict[str, str]
    transactions: int
    baseline_transactions: int
    conversion_rate: float
    baseline_conversion_rate: float
    conversion_drop: float
    revenue_at_risk: Decimal
    evidence: tuple[str, ...]


def _conversion(rows: list[Transaction]) -> float:
    if not rows:
        return 0.0
    return sum(r.status is TransactionStatus.SUCCESS for r in rows) / len(rows)


def _failed_revenue(rows: list[Transaction]) -> Decimal:
    return sum(
        (r.amount for r in rows if r.status is not TransactionStatus.SUCCESS),
        Decimal("0"),
    )


def detect_cohort_leaks(
    transactions: Iterable[Transaction],
    *,
    min_transactions: int = 30,
    min_drop: float = 0.15,
) -> list[LeakCandidate]:
    """Find cohort conversion drops without using leak-injection ground truth.

    For each payment-method/device cohort we compare the cohort's conversion
    against the complementary population. This intentionally remains
    deterministic and explainable; statistical significance can be added after
    the first end-to-end evaluation.
    """
    rows = list(transactions)
    candidates: list[LeakCandidate] = []

    methods = list(PaymentMethod)
    devices = list(DeviceType)

    for method, device in product(methods, devices):
        cohort = [
            r for r in rows
            if r.payment_method is method and r.device is device
            and 20 <= r.occurred_at.hour < 23
        ]
        baseline = [
            r for r in rows
            if not (r.payment_method is method and r.device is device and 20 <= r.occurred_at.hour < 23)
        ]

        if len(cohort) < min_transactions or len(baseline) < min_transactions:
            continue

        cohort_rate = _conversion(cohort)
        baseline_rate = _conversion(baseline)
        drop = baseline_rate - cohort_rate

        if drop < min_drop:
            continue

        candidates.append(
            LeakCandidate(
                title=f"{method.value.upper()} conversion degradation on {device.value}",
                cohort={"payment_method": method.value, "device": device.value},
                transactions=len(cohort),
                baseline_transactions=len(baseline),
                conversion_rate=cohort_rate,
                baseline_conversion_rate=baseline_rate,
                conversion_drop=drop,
                revenue_at_risk=_failed_revenue(cohort),
                evidence=(
                    f"Cohort conversion is {cohort_rate:.1%}.",
                    f"Complementary population conversion is {baseline_rate:.1%}.",
                    f"Conversion gap is {drop:.1%}.",
                ),
            )
        )

    return sorted(
        candidates,
        key=lambda candidate: candidate.revenue_at_risk,
        reverse=True,
    )
