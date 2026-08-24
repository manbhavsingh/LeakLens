from __future__ import annotations

from dataclasses import dataclass


ALLOWED_ACTIONS = {
    "PAYMENT_METHOD_EXPERIMENT",
    "RECOVERY_PAYMENT_LINK",
    "DO_NOT_INTERVENE",
}


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    action: str
    reason: str


def validate_action(
    action: str,
    *,
    confidence: float,
    expected_revenue: float,
    max_expected_revenue: float = 100_000.0,
) -> PolicyDecision:
    if action not in ALLOWED_ACTIONS:
        return PolicyDecision(False, action, "Action is not in the bounded intervention allowlist.")

    if not 0.0 <= confidence <= 1.0:
        return PolicyDecision(False, action, "Confidence must be between 0 and 1.")

    if expected_revenue < 0:
        return PolicyDecision(False, action, "Expected revenue cannot be negative.")

    if expected_revenue > max_expected_revenue:
        return PolicyDecision(False, action, "Expected revenue exceeds the configured intervention limit.")

    if action != "DO_NOT_INTERVENE" and confidence < 0.70:
        return PolicyDecision(False, action, "Interventions require at least 0.70 confidence.")

    return PolicyDecision(True, action, "Action satisfies bounded intervention policy.")
