import json

from app.agent import LeakLensAgent
from app.leaks import inject_upi_android_evening_degradation
from app.synthetic import generate_transactions


class MockLLM:
    def __init__(self):
        self.calls = 0

    def complete(self, *, messages, tools):
        self.calls += 1
        # After a couple of tool steps, return a bounded final decision
        if self.calls >= 2:
            return {
                "content": json.dumps({
                    "hypothesis": "Evening degradation observed in UPI/Android cohort",
                    "confidence": 0.88,
                    "action": "PAYMENT_METHOD_EXPERIMENT",
                    "expected_revenue": 5000,
                    "rationale": "Evidence supports bounded experiment.",
                    "evidence": ["Conversion drop exceeds 0.15."],
                }),
                "tool_calls": [],
            }
        return {
            "content": None,
            "tool_calls": [{
                "id": "call-1",
                "name": "find_revenue_leaks",
                "arguments": {"min_transactions": 30, "min_drop": 0.15},
            }],
        }


def test_agent_produces_auditable_trace() -> None:
    rows = generate_transactions(count=10000, seed=42)
    inject_upi_android_evening_degradation(rows)

    agent = LeakLensAgent(MockLLM(), rows)
    finding = {"title": "leak", "cohort": {"payment_method": "upi", "device": "android"}}
    result = agent.run(finding)

    assert result
    assert result.steps
    assert any(step.name == "find_revenue_leaks" for step in result.steps)
    assert result.policy.allowed is True
    assert result.decision["action"] in {
        "PAYMENT_METHOD_EXPERIMENT",
        "RECOVERY_PAYMENT_LINK",
        "DO_NOT_INTERVENE",
    }
