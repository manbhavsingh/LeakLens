from app.e2e import run_evaluation


def test_end_to_end_evaluation_finds_ground_truth_leak() -> None:
    result = run_evaluation(count=10_000, seed=42)

    assert result.transaction_count == 10_000
    assert result.injected_leak == "upi_android_evening_degradation"
    assert result.ground_truth_revenue_at_risk > 0
    assert result.detected_findings > 0
    assert result.top_finding is not None
    assert result.top_finding["cohort"] == {"payment_method": "upi", "device": "android"}
    assert result.hypothesis is not None
    assert result.recommended_action == "PAYMENT_METHOD_EXPERIMENT"
    assert result.policy_allowed is True
