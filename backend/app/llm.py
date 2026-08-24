from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Protocol


SYSTEM_PROMPT = """You are LeakLens, a revenue-recovery investigation agent.
Investigate merchant revenue leakage using only the provided typed tools.
Treat findings as evidence, not proof of causality. Gather enough evidence before
recommending an intervention. You may recommend only PAYMENT_METHOD_EXPERIMENT,
RECOVERY_PAYMENT_LINK, or DO_NOT_INTERVENE. Never directly execute payment APIs.
The deterministic policy gate has final authority over every intervention."""


class Planner(Protocol):
    def decide(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> dict[str, Any]: ...


@dataclass
class JsonPlanner:
    """Small adapter around any OpenAI-compatible chat client.

    The repository intentionally does not bundle credentials or a vendor SDK.
    The application can inject a client implementing `chat.completions.create`
    and this adapter will normalize its structured JSON response.
    """

    client: Any
    model: str

    def decide(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> dict[str, Any]:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content
        if not content:
            raise ValueError("LLM returned an empty decision.")
        decision = json.loads(content)
        if not isinstance(decision, dict):
            raise ValueError("LLM decision must be a JSON object.")
        return decision
