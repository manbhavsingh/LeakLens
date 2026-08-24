from app.agent import LeakLensAgent
from app.leaks import inject_upi_android_evening_degradation
from app.synthetic import generate_transactions


def test_agent_produces_auditable_trace() -> None:
    rows = generate_transactions(count=10000, seed=42)
    inject_upi_android_evening_degradation(rows)

    agent = LeakLensAgent(rows)
    results = agent.run()

    assert results
    assert results[0].steps
    assert results[0].steps[0].tool == "find_revenue_leaks"
    assert results[0].policy_allowed is True
    assert results[0].action in {
        "PAYMENT_METHOD_EXPERIMENT",
        "RECOVERY_PAYMENT_LINK",
        "DO_NOT_INTERVENE",
    }
