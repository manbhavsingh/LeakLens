from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.persistence import PersistenceBase, RecoveryIntervention, WebhookEvent, mark_intervention_paid, persist_event, persist_intervention
from app.recovery import InterventionRecord
from app.razorpay import PaymentEvent


def test_event_and_intervention_persistence() -> None:
    engine = create_engine("sqlite://")
    PersistenceBase.metadata.create_all(engine)

    event = PaymentEvent(
        event_id="evt-1",
        event_type="payment.failed",
        payment_id="pay-1",
        order_id="ord-1",
        amount=499900,
        status="failed",
        raw={"event": "payment.failed"},
    )

    with Session(engine) as session:
        assert persist_event(session, event) is True
        assert persist_event(session, event) is False

        record = InterventionRecord("recovery-1", "customer-1", Decimal("4999"))
        persist_intervention(session, record)
        assert mark_intervention_paid(session, "recovery-1", "pay-2", Decimal("4999")) is True
        assert mark_intervention_paid(session, "recovery-1", "pay-2", Decimal("4999")) is False

        stored = session.get(RecoveryIntervention, "recovery-1")
        assert stored is not None
        assert stored.paid_amount == Decimal("4999")
