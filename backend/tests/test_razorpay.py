import hashlib
import hmac
import json

import pytest

from app.event_store import EventStore
from app.razorpay import WebhookVerificationError, parse_payment_webhook


def payload() -> bytes:
    return json.dumps({
        "event": "payment.failed",
        "payload": {"payment": {"entity": {
            "id": "pay_test_123",
            "order_id": "order_test_123",
            "amount": 499900,
            "status": "failed",
        }}},
    }).encode()


def test_webhook_signature_and_normalization() -> None:
    body = payload()
    secret = "test-secret"
    signature = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    event = parse_payment_webhook(body, "evt_1", signature, secret)

    assert event.event_id == "evt_1"
    assert event.event_type == "payment.failed"
    assert event.payment_id == "pay_test_123"
    assert event.amount == 499900


def test_invalid_signature_is_rejected() -> None:
    with pytest.raises(WebhookVerificationError):
        parse_payment_webhook(payload(), "evt_1", "bad", "test-secret")


def test_duplicate_event_is_ignored() -> None:
    body = payload()
    secret = "test-secret"
    signature = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    event = parse_payment_webhook(body, "evt_duplicate", signature, secret)

    store = EventStore()
    assert store.add_if_new(event) is True
    assert store.add_if_new(event) is False
    assert store.count() == 1
