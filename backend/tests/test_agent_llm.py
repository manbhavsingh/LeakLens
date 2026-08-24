import json

from app.agent import LeakLensAgent
from app.synthetic import generate_transactions
from app.tool_dispatcher import InvestigatorToolDispatcher


class FakeLLM:
    def __init__(self):
        self.calls = 0

    def complete(self, *, messages, tools):
        self.calls += 1
        if self.calls == 1:
            return {
                "content": None,
                "tool_calls": [{
                    "id": "call-1",
                    "name": "get_payment_failure_breakdown",
                    "arguments": {"payment_method": "upi"},
                }],
            }
        return {
            "content": json.dumps({
                "hypothesis": "UPI failures may be contributing to the observed leakage.",
                "confidence": 0.82,
                "action": "PAYMENT_METHOD_EXPERIMENT",
                "expected_revenue": 5000,
                "rationale": "Evidence supports testing an alternate payment path.",
                "evidence": ["UPI failure breakdown was inspected."],
            }),
            "tool_calls": [],
        }


def test_llm_agent_executes_tool_then_returns_policy_checked_decision() -> None:
    rows = generate_transactions(count=1000, seed=42)
    agent = LeakLensAgent(FakeLLM(), rows)
    result = agent.run({"title": "demo finding", "revenue_at_risk": 5000})

    assert result.policy.allowed is True
    assert result.decision["action"] == "PAYMENT_METHOD_EXPERIMENT"
    assert len(result.steps) == 2
    assert result.steps[0].name == "get_payment_failure_breakdown"
    assert result.steps[1].name == "final_decision"
