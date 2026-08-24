from app.detector import detect_cohort_leaks
from app.leaks import inject_upi_android_evening_degradation
from app.synthetic import generate_transactions


def test_detector_finds_injected_upi_android_leak() -> None:
    rows = generate_transactions(count=10000, seed=42)
    truth = inject_upi_android_evening_degradation(rows)

    candidates = detect_cohort_leaks(rows, min_transactions=30, min_drop=0.15)

    assert candidates
    top = candidates[0]
    assert top.cohort["payment_method"] == "upi"
    assert top.cohort["device"] == "android"
    assert top.revenue_at_risk > 0
    assert truth.revenue_at_risk > 0


def test_detector_does_not_emit_small_cohorts() -> None:
    rows = generate_transactions(count=20, seed=3)
    assert detect_cohort_leaks(rows, min_transactions=30) == []
