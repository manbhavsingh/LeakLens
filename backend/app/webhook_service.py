from __future__ import annotations

from .event_store import EventStore
from .jobs import JobQueue
from .razorpay import PaymentEvent


class WebhookService:
    def __init__(self, event_store: EventStore, job_queue: JobQueue):
        self.event_store = event_store
        self.job_queue = job_queue

    def accept(self, event: PaymentEvent) -> str | None:
        if not self.event_store.add_if_new(event):
            return None
        job = self.job_queue.enqueue(event_id=event.event_id, job_type="investigate_payment_event")
        return job.id
