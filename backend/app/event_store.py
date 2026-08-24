from __future__ import annotations

from dataclasses import dataclass

from .razorpay import PaymentEvent


@dataclass
class EventStore:
    """Small deterministic store for the webhook demo.

    PostgreSQL persistence will replace this implementation before deployment.
    """

    events: dict[str, PaymentEvent] | None = None

    def __post_init__(self) -> None:
        if self.events is None:
            self.events = {}

    def add_if_new(self, event: PaymentEvent) -> bool:
        assert self.events is not None
        if event.event_id in self.events:
            return False
        self.events[event.event_id] = event
        return True

    def count(self) -> int:
        return len(self.events or {})
