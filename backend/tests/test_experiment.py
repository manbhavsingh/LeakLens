from decimal import Decimal

import pytest

from app.experiment import evaluate_conversion_experiment


def test_experiment_reports_incremental_lift_and_revenue() -> None:
    result = evaluate_conversion_experiment(
        control_successes=40,
        control_total=100,
        treatment_successes=55,
        treatment_total=100,
        control_revenue=Decimal("40000"),
        treatment_revenue=Decimal("55000"),
    )

    assert result.control_conversion == pytest.approx(0.4)
    assert result.treatment_conversion == pytest.approx(0.55)
    assert result.incremental_lift == pytest.approx(0.15)
    assert result.incremental_revenue == Decimal("15000")
