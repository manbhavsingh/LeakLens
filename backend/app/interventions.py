from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from .policy import validate_action


class PaymentProvider(Protocol):
    def create_payment_link(self, *, amount: int, reference_id: str, description: str) -> dict[str, Any]: ...


@dataclass(frozen=True)
class InterventionResult:
    action: str
    executed: bool
    reference_id: str
    provider_response: dict[str, Any]
    reason: str


class InterventionExecutor:
    def __init__(self, provider: PaymentProvider):
        self.provider = provider

    def execute(
        self,
        *,
        action: str,
        confidence: float,
        expected_revenue: float,
        reference_id: str,
        amount: int,
        max_expected_revenue: float = 100_000.0,
    ) -> InterventionResult:
        policy = validate_action(
            action,
            confidence=confidence,
            expected_revenue=expected_revenue,
            max_expected_revenue=max_expected_revenue,
        )
        if not policy.allowed:
            return InterventionResult(action, False, reference_id, {}, policy.reason)

        if action == "DO_NOT_INTERVENE":
            return InterventionResult(action, False, reference_id, {}, "Policy selected no intervention.")

        if action != "RECOVERY_PAYMENT_LINK":
            return InterventionResult(
                action,
                False,
                reference_id,
                {},
                "This intervention requires an experiment executor and is not directly executed.",
            )

        response = self.provider.create_payment_link(
            amount=amount,
            reference_id=reference_id,
            description="LeakLens bounded revenue recovery",
        )
        return InterventionResult(
            action,
            True,
            reference_id,
            response,
            "Recovery payment link created after policy approval.",
        )


class FakePaymentProvider:
    """Deterministic provider used for tests; no external money movement."""

    def create_payment_link(self, *, amount: int, reference_id: str, description: str) -> dict[str, Any]:
        return {
            "id": f"plink_test_{reference_id}",
            "short_url": f"https://example.test/pay/{reference_id}",
            "amount": amount,
            "description": description,
        }
