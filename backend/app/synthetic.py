from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from .models import DeviceType, PaymentMethod, Transaction, TransactionStatus


FAILURE_REASONS = ("timeout", "bank_decline", "insufficient_funds", "unknown")


def generate_transactions(
    count: int = 1000,
    seed: int = 42,
    merchant_id: str = "merchant_demo",
) -> list[Transaction]:
    """Generate a deterministic merchant universe for agent evaluation.

    The baseline intentionally has no injected anomaly yet. Leak injection will
    be added as a separate layer so ground truth remains explicit and testable.
    """
    rng = random.Random(seed)
    start = datetime.now(timezone.utc) - timedelta(days=14)
    rows: list[Transaction] = []

    methods = list(PaymentMethod)
    devices = list(DeviceType)

    for index in range(count):
        method = rng.choice(methods)
        device = rng.choice(devices)
        amount = Decimal(str(rng.choice([499, 799, 1299, 2499, 4999, 9999])))
        status = TransactionStatus.SUCCESS if rng.random() < 0.78 else rng.choice(
            [TransactionStatus.FAILED, TransactionStatus.ABANDONED]
        )
        failure_reason = None
        if status is TransactionStatus.FAILED:
            failure_reason = rng.choice(FAILURE_REASONS)

        rows.append(
            Transaction(
                event_id=f"synthetic-{seed}-{index}",
                merchant_id=merchant_id,
                customer_id=f"customer-{rng.randint(1, max(1, count // 5))}",
                amount=amount,
                status=status,
                payment_method=method,
                device=device,
                failure_reason=failure_reason,
                occurred_at=start + timedelta(minutes=rng.randint(0, 14 * 24 * 60)),
            )
        )

    return rows
