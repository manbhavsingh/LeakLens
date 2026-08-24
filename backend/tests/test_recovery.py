from decimal import Decimal

from app.recovery import InterventionRecord, InterventionStatus, RecoveryLedger
from app.recovery_webhook import process_payment_event
from app.razorpay import PaymentEvent


def test_paid_event_is_attributed_once() -> None:
    ledger = RecoveryLedger()
    ledger.register(InterventionRecord(
        reference_id="recovery-1",
        customer_id="customer-1",
        amount=Decimal("4999"),
    ))

    event = PaymentEvent(
        event_id="evt-1",
        event_type="payment_link.paid",
        payment_id="pay-1",
        order_id=None,
        amount=499900,
        status="captured",
        raw={
            "event": "payment_link.paid",
            "payload": {
                "payment": {"entity": {"id": "pay-1", "amount": 499900}},
                "payment_link": {"entity": {"reference_id": "recovery-1", "amount": 499900}},
            },
        },
    )

    assert process_payment_event(event, ledger) is True
    assert process_payment_event(event, ledger) is False
    assert ledger.records["recovery-1"].status is InterventionStatus.PAID
    assert ledger.recovered_revenue() == Decimal("4999")
