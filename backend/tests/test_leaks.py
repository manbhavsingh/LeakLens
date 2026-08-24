from app.leaks import inject_upi_android_evening_degradation
from app.synthetic import generate_transactions
from app.models import DeviceType, PaymentMethod


def test_upi_android_evening_leak_is_reproducible() -> None:
    rows = generate_transactions(count=5000, seed=11)
    result = inject_upi_android_evening_degradation(rows)

    matching = [
        row for row in rows
        if row.payment_method is PaymentMethod.UPI
        and row.device is DeviceType.ANDROID
        and 20 <= row.occurred_at.hour < 23
    ]

    assert result.name == "upi_android_evening_degradation"
    assert result.affected_transaction_ids == tuple(row.event_id for row in sorted(matching, key=lambda row: row.event_id))
    assert result.leaked_conversion == 0.52
    assert result.revenue_at_risk >= 0
