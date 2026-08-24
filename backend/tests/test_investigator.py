from app.investigator import investigate
from app.leaks import inject_upi_android_evening_degradation
from app.policy import validate_action
from app.synthetic import generate_transactions


def test_investigator_forms_evidence_backed_hypothesis() -> None:
    rows = generate_transactions(count=10000, seed=42)
    inject_upi_android_evening_degradation(rows)

    investigations = investigate(rows)

    assert investigations
    top = investigations[0]
    assert top.finding.revenue_at_risk > 0
    assert top.evidence
    assert "PAYMENT_METHOD_EXPERIMENT" == top.recommended_action


def test_policy_rejects_weak_intervention() -> None:
    decision = validate_action(
        "PAYMENT_METHOD_EXPERIMENT",
        confidence=0.69,
        expected_revenue=5000,
    )
    assert decision.allowed is False


def test_policy_allows_bounded_intervention() -> None:
    decision = validate_action(
        "PAYMENT_METHOD_EXPERIMENT",
        confidence=0.85,
        expected_revenue=5000,
    )
    assert decision.allowed is True
