from decimal import Decimal
from datetime import datetime, timezone

from app.analytics import calculate_metrics
from app.models import DeviceType, PaymentMethod, Transaction, TransactionStatus


def tx(status: TransactionStatus, amount: str) -> Transaction:
    return Transaction(
        event_id=f"evt-{status}-{amount}",
        merchant_id="m1",
        customer_id="c1",
        amount=Decimal(amount),
        status=status,
        payment_method=PaymentMethod.UPI,
        device=DeviceType.ANDROID,
        occurred_at=datetime.now(timezone.utc),
    )


def test_calculate_metrics() -> None:
    metrics = calculate_metrics([
        tx(TransactionStatus.SUCCESS, "100"),
        tx(TransactionStatus.SUCCESS, "50"),
        tx(TransactionStatus.FAILED, "75"),
    ])

    assert metrics.transactions == 3
    assert metrics.successful_transactions == 2
    assert metrics.conversion_rate == 2 / 3
    assert metrics.gross_revenue == Decimal("150")
    assert metrics.failed_revenue == Decimal("75")
