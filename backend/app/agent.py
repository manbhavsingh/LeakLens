from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable

from .investigator import investigate
from .models import Transaction
from .policy import validate_action


Tool = Callable[..., Any]


@dataclass(frozen=True)
class AgentStep:
    tool: str
    arguments: dict[str, Any]
    observation: Any


@dataclass(frozen=True)
class AgentResult:
    hypothesis: str
    action: str
    confidence: float
    expected_revenue: float
    evidence: tuple[str, ...]
    steps: tuple[AgentStep, ...]
    policy_allowed: bool
    policy_reason: str


class LeakLensAgent:
    """Agent boundary for LeakLens.

    The current implementation uses deterministic tool calls so the entire
    investigation is executable without an API key. A model adapter can later
    replace the planner while keeping the same tools and policy boundary.
    """

    def __init__(self, transactions: list[Transaction]):
        self.transactions = transactions
        self.steps: list[AgentStep] = []

    def run(self) -> list[AgentResult]:
        investigations = investigate(self.transactions)
        results: list[AgentResult] = []

        for item in investigations:
            self.steps.append(
                AgentStep(
                    tool="find_revenue_leaks",
                    arguments={},
                    observation={
                        "title": item.finding.title,
                        "cohort": item.finding.cohort,
                        "revenue_at_risk": float(item.finding.revenue_at_risk),
                    },
                )
            )
            self.steps.append(
                AgentStep(
                    tool="get_payment_failure_breakdown",
                    arguments={"payment_method": item.finding.cohort["payment_method"]},
                    observation=item.failure_breakdown,
                )
            )

            policy = validate_action(
                item.recommended_action,
                confidence=item.confidence,
                expected_revenue=float(item.finding.revenue_at_risk),
            )

            results.append(
                AgentResult(
                    hypothesis=item.hypothesis,
                    action=item.recommended_action,
                    confidence=item.confidence,
                    expected_revenue=float(item.finding.revenue_at_risk),
                    evidence=item.evidence,
                    steps=tuple(self.steps),
                    policy_allowed=policy.allowed,
                    policy_reason=policy.reason,
                )
            )

        return results

    @staticmethod
    def tool_schemas() -> list[dict[str, Any]]:
        """OpenAI-compatible function schemas for a future model adapter."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "find_revenue_leaks",
                    "description": "Find cohort-level revenue leakage candidates.",
                    "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_payment_failure_breakdown",
                    "description": "Break down payment failures by reason.",
                    "parameters": {
                        "type": "object",
                        "properties": {"payment_method": {"type": "string"}},
                        "additionalProperties": False,
                    },
                },
            },
        ]

    def debug_trace(self) -> str:
        return json.dumps(
            [
                {"tool": step.tool, "arguments": step.arguments, "observation": step.observation}
                for step in self.steps
            ],
            indent=2,
            default=str,
        )
