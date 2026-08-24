import json
import hashlib
import hmac

from app.event_store import EventStore
from app.jobs import JobQueue
from app.razorpay import parse_payment_webhook
from app.webhook_service import WebhookService


def test_webhook_service_enqueues_only_new_events() -> None:
    body = json.dumps({"event": "payment.failed", "payload": {"payment": {"entity": {"id": "pay-1", "amount": 100}}}}).encode()
    secret = "secret"
    signature = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    event = parse_payment_webhook(body, "evt-1", signature, secret)

    service = WebhookService(EventStore(), JobQueue())
    first_job = service.accept(event)
    second_job = service.accept(event)

    assert first_job is not None
    assert second_job is None
