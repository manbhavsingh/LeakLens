from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal
from typing import Any

from .detector import detect_cohort_leaks
from .experiment import evaluate_conversion_experiment
from .investigator import investigate
from .leaks import inject_upi_android_evening_degradation
from .policy import validate_action
from .synthetic import generate_transactions


@dataclass(frozen=True)
class Evaluation:
    transaction_count: int
    injected_leak: str
    ground_truth_revenue_at_risk: Decimal
    detected_findings: int
    top_finding: dict[str, Any] | None
    hypothesis: str | None
    recommended_action: str | None
    policy_allowed: bool | None


def run_evaluation(*, count: int = 10_000, seed: int = 42) -> Evaluation:
    rows = generate_transactions(count=count, seed=seed)
    truth = inject_upi_android_evening_degradation(rows, seed=seed)
    findings = detect_cohort_leaks(rows)
    investigations = investigate(rows)

    top = findings[0] if findings else None
    top_investigation = investigations[0] if investigations else None

    if top_investigation:
        policy = validate_action(
            top_investigation.recommended_action,
            confidence=top_investigation.confidence,
            expected_revenue=float(top_investigation.finding.revenue_at_risk),
            max_expected_revenue=250_000.0,
        )
        allowed = policy.allowed
    else:
        allowed = None

    return Evaluation(
        transaction_count=len(rows),
        injected_leak=truth.name,
        ground_truth_revenue_at_risk=truth.revenue_at_risk,
        detected_findings=len(findings),
        top_finding=(
            {
                "title": top.title,
                "cohort": top.cohort,
                "conversion_rate": top.conversion_rate,
                "baseline_conversion_rate": top.baseline_conversion_rate,
                "conversion_drop": top.conversion_drop,
                "revenue_at_risk": str(top.revenue_at_risk),
            }
            if top else None
        ),
        hypothesis=top_investigation.hypothesis if top_investigation else None,
        recommended_action=top_investigation.recommended_action if top_investigation else None,
        policy_allowed=allowed,
    )
