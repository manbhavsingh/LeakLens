from __future__ import annotations

import json
from typing import Any
from uuid import uuid4

from .agent import LeakLensAgent
from .investigation_store import InvestigationResultStore


class InvestigationJobHandler:
    """Turn a claimed payment-event job into one persisted agent decision."""

    def __init__(self, agent: LeakLensAgent, results: InvestigationResultStore):
        self.agent = agent
        self.results = results

    def __call__(self, job: dict[str, Any], event_loader) -> dict[str, Any]:
        event = event_loader(job["event_id"])
        if event is None:
            raise RuntimeError(f"event not found: {job['event_id']}")

        finding = self._build_finding(event)
        outcome = self.agent.investigate(finding)
        decision = {
            "decision": outcome.decision,
            "policy": {
                "allowed": outcome.policy.allowed,
                "action": outcome.policy.action,
                "reason": outcome.policy.reason,
            },
            "trace": list(outcome.trace),
        }
        self.results.save_once(
            result_id=str(uuid4()),
            event_id=job["event_id"],
            status="completed",
            result=decision,
        )
        return decision

    @staticmethod
    def _build_finding(event: dict[str, Any]) -> dict[str, Any]:
        return {
            "source": "razorpay_webhook",
            "event_id": event.get("event_id"),
            "event_type": event.get("event_type"),
            "payment_id": event.get("payment_id"),
            "amount": event.get("amount"),
            "status": event.get("status"),
            "context": event.get("raw", {}),
        }
