from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Protocol

from .models import Transaction
from .policy import PolicyDecision, validate_action
from .tool_dispatcher import InvestigatorToolDispatcher, ToolExecutionError
from .tool_schema import TOOLS


SYSTEM_PROMPT = """You are LeakLens, an evidence-first revenue investigation agent.
Investigate revenue leakage using only the provided read-only tools. Treat
explanations as hypotheses, not proven causality. Gather enough evidence before
recommending an intervention. You may recommend only PAYMENT_METHOD_EXPERIMENT,
RECOVERY_PAYMENT_LINK, or DO_NOT_INTERVENE. The policy engine makes the final
authorization decision. Return final decisions as JSON with fields: hypothesis,
confidence, action, expected_revenue, rationale, evidence."""


class LLMClient(Protocol):
    def complete(self, *, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> dict[str, Any]: ...


@dataclass(frozen=True)
class AgentStep:
    kind: str
    name: str
    arguments: dict[str, Any]
    result: Any


@dataclass(frozen=True)
class AgentResult:
    decision: dict[str, Any]
    policy: PolicyDecision
    steps: tuple[AgentStep, ...]


class LeakLensAgent:
    """Bounded LLM tool-calling loop with a deterministic policy boundary."""

    def __init__(self, llm: LLMClient, transactions: list[Transaction], max_steps: int = 6):
        self.llm = llm
        self.dispatcher = InvestigatorToolDispatcher(transactions)
        self.max_steps = max_steps

    def run(self, finding: dict[str, Any]) -> AgentResult:
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps({"finding": finding})},
        ]
        steps: list[AgentStep] = []

        for _ in range(self.max_steps):
            response = self.llm.complete(messages=messages, tools=TOOLS)
            tool_calls = response.get("tool_calls") or []

            if not tool_calls:
                decision = self._parse_decision(response.get("content"))
                policy = validate_action(
                    decision["action"],
                    confidence=float(decision["confidence"]),
                    expected_revenue=float(decision["expected_revenue"]),
                )
                steps.append(AgentStep("decision", "final_decision", {}, decision))
                return AgentResult(decision=decision, policy=policy, steps=tuple(steps))

            messages.append({
                "role": "assistant",
                "content": response.get("content"),
                "tool_calls": tool_calls,
            })

            for call in tool_calls:
                name = call.get("name")
                arguments = call.get("arguments") or {}
                try:
                    result = self.dispatcher.execute(name, arguments)
                    steps.append(AgentStep("tool", name, arguments, result))
                except ToolExecutionError as exc:
                    result = {"error": str(exc)}
                    steps.append(AgentStep("tool_error", name or "unknown", arguments, result))

                messages.append({
                    "role": "tool",
                    "name": name,
                    "tool_call_id": call.get("id", name),
                    "content": json.dumps(result, default=str),
                })

        raise RuntimeError("Agent exceeded its bounded investigation step limit")

    @staticmethod
    def _parse_decision(content: Any) -> dict[str, Any]:
        if not isinstance(content, str):
            raise ValueError("LLM must return JSON when it has no tool calls")
        try:
            decision = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ValueError("LLM final response must be valid JSON") from exc

        required = {"hypothesis", "confidence", "action", "expected_revenue", "rationale", "evidence"}
        missing = required - decision.keys()
        if missing:
            raise ValueError(f"LLM decision missing fields: {sorted(missing)}")
        return decision
