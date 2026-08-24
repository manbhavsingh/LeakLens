from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from .recovery import InterventionStatus, RecoveryLedger


@dataclass(frozen=True)
class RecoveryMetrics:
    interventions: int
    paid_interventions: int
    recovery_rate: float
    recovered_revenue: Decimal


def calculate_recovery_metrics(ledger: RecoveryLedger) -> RecoveryMetrics:
    records = list(ledger.records.values())
    paid = sum(record.status is InterventionStatus.PAID for record in records)
    return RecoveryMetrics(
        interventions=len(records),
        paid_interventions=paid,
        recovery_rate=paid / len(records) if records else 0.0,
        recovered_revenue=ledger.recovered_revenue(),
    )
