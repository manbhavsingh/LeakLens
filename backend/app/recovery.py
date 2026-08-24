from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum


class InterventionStatus(StrEnum):
    CREATED = "created"
    PAID = "paid"
    EXPIRED = "expired"
    FAILED = "failed"


@dataclass
class InterventionRecord:
    reference_id: str
    customer_id: str | None
    amount: Decimal
    status: InterventionStatus = InterventionStatus.CREATED
    paid_amount: Decimal = Decimal("0")
    payment_id: str | None = None


class RecoveryLedger:
    """Idempotent attribution ledger for recovery interventions."""

    def __init__(self) -> None:
        self.records: dict[str, InterventionRecord] = {}
        self.processed_payment_ids: set[str] = set()

    def register(self, record: InterventionRecord) -> None:
        if record.reference_id in self.records:
            return
        self.records[record.reference_id] = record

    def mark_paid(self, *, reference_id: str, payment_id: str, amount: Decimal) -> bool:
        if payment_id in self.processed_payment_ids:
            return False
        record = self.records.get(reference_id)
        if record is None:
            return False
        self.processed_payment_ids.add(payment_id)
        record.status = InterventionStatus.PAID
        record.payment_id = payment_id
        record.paid_amount = amount
        return True

    def recovered_revenue(self) -> Decimal:
        return sum((r.paid_amount for r in self.records.values()), Decimal("0"))
