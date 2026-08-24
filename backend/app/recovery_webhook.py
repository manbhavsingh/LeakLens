from __future__ import annotations

from decimal import Decimal

from .recovery import RecoveryLedger
from .razorpay import PaymentEvent


def process_payment_event(event: PaymentEvent, ledger: RecoveryLedger) -> bool:
    """Attribute a captured/paid payment to an intervention by reference_id.

    Razorpay Payment Link webhook payloads can carry the reference_id on the
    payment-link entity. Normalized events retain the raw payload so the
    attribution layer can inspect provider-specific metadata safely.
    """
    if event.event_type not in {"payment.captured", "payment_link.paid", "order.paid"}:
        return False

    payment = event.raw.get("payload", {}).get("payment", {}).get("entity", {})
    payment_link = event.raw.get("payload", {}).get("payment_link", {}).get("entity", {})
    reference_id = payment_link.get("reference_id") or payment.get("reference_id")
    payment_id = event.payment_id or payment.get("id")
    amount = payment.get("amount") or payment_link.get("amount")

    if not reference_id or not payment_id or amount is None:
        return False

    return ledger.mark_paid(
        reference_id=reference_id,
        payment_id=payment_id,
        amount=Decimal(str(amount)) / Decimal("100"),
    )
