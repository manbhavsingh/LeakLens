from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class ExperimentResult:
    control_conversion: float
    treatment_conversion: float
    incremental_lift: float
    control_revenue: Decimal
    treatment_revenue: Decimal
    incremental_revenue: Decimal


def evaluate_conversion_experiment(
    *,
    control_successes: int,
    control_total: int,
    treatment_successes: int,
    treatment_total: int,
    control_revenue: Decimal,
    treatment_revenue: Decimal,
) -> ExperimentResult:
    control_rate = control_successes / control_total if control_total else 0.0
    treatment_rate = treatment_successes / treatment_total if treatment_total else 0.0

    return ExperimentResult(
        control_conversion=control_rate,
        treatment_conversion=treatment_rate,
        incremental_lift=treatment_rate - control_rate,
        control_revenue=control_revenue,
        treatment_revenue=treatment_revenue,
        incremental_revenue=treatment_revenue - control_revenue,
    )
