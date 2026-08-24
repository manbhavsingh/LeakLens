from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class LLMAPIError(RuntimeError):
    pass


class OpenAICompatibleClient:
    """Minimal OpenAI-compatible chat-completions client.

    Credentials are read at runtime; none are stored in the repository.
    """

    def __init__(self, api_key: str, model: str, base_url: str = "https://api.openai.com/v1", timeout: float = 60.0):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def complete(self, *, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> dict[str, Any]:
        body = json.dumps({
            "model": self.model,
            "messages": messages,
            "tools": tools,
            "tool_choice": "auto",
        }).encode()
        request = Request(
            f"{self.base_url}/chat/completions",
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                payload = json.loads(response.read())
        except (HTTPError, URLError, TimeoutError) as exc:
            raise LLMAPIError("LLM request failed") from exc

        try:
            message = payload["choices"][0]["message"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMAPIError("LLM response did not contain a chat message") from exc

        normalized: dict[str, Any] = {"content": message.get("content")}
        calls = []
        for call in message.get("tool_calls", []) or []:
            function = call.get("function", {})
            raw_arguments = function.get("arguments", "{}")
            try:
                arguments = json.loads(raw_arguments) if isinstance(raw_arguments, str) else raw_arguments
            except json.JSONDecodeError as exc:
                raise LLMAPIError("LLM returned invalid tool arguments") from exc
            calls.append({
                "id": call.get("id"),
                "name": function.get("name"),
                "arguments": arguments,
            })
        normalized["tool_calls"] = calls
        return normalized
