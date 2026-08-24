from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass
from typing import Any


class WebhookVerificationError(ValueError):
    pass


def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


@dataclass(frozen=True)
class PaymentEvent:
    event_id: str
    event_type: str
    payment_id: str | None
    order_id: str | None
    amount: int | None
    status: str | None
    raw: dict[str, Any]


def parse_payment_webhook(payload: bytes, event_id: str, signature: str, secret: str) -> PaymentEvent:
    if not verify_webhook_signature(payload, signature, secret):
        raise WebhookVerificationError("Invalid Razorpay webhook signature")

    data = json.loads(payload)
    event_type = data.get("event", "unknown")
    payment = data.get("payload", {}).get("payment", {}).get("entity", {})
    order_id = payment.get("order_id")

    return PaymentEvent(
        event_id=event_id,
        event_type=event_type,
        payment_id=payment.get("id"),
        order_id=order_id,
        amount=payment.get("amount"),
        status=payment.get("status"),
        raw=data,
    )
