from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from decimal import Decimal
from typing import Any

from .agent import LLMClient
from .detector import detect_cohort_leaks
from .experiment import evaluate_conversion_experiment
from .interventions import FakePaymentProvider, InterventionExecutor
from .investigator import investigate
from .leaks import inject_upi_android_evening_degradation
from .llm_client import OpenAICompatibleClient
from .policy import validate_action
from .recovery import RecoveryLedger
from .recovery_metrics import RecoveryMetrics, calculate_recovery_metrics
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
    intervention: dict[str, Any] | None
    recovery: dict[str, Any] | None
    agent_used: bool


def _get_llm_client() -> LLMClient | None:
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY")
    if not api_key:
        return None
    try:
        return OpenAICompatibleClient(
            api_key=api_key,
            model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
        )
    except Exception:
        return None


def run_evaluation(*, count: int = 10_000, seed: int = 42) -> Evaluation:
    rows = generate_transactions(count=count, seed=seed)
    truth = inject_upi_android_evening_degradation(rows, seed=seed)

    llm = _get_llm_client()
    agent_used = llm is not None

    findings = detect_cohort_leaks(rows)
    investigations = investigate(rows, llm=llm)

    top = findings[0] if findings else None
    top_investigation = investigations[0] if investigations else None

    intervention_result = None
    if top_investigation:
        policy = validate_action(
            top_investigation.recommended_action,
            confidence=top_investigation.confidence,
            expected_revenue=float(top_investigation.finding.revenue_at_risk),
            max_expected_revenue=250_000.0,
        )
        allowed = policy.allowed

        if allowed:
            executor = InterventionExecutor(FakePaymentProvider())
            intervention_result = executor.execute(
                action=top_investigation.recommended_action,
                confidence=top_investigation.confidence,
                expected_revenue=float(top_investigation.finding.revenue_at_risk),
                reference_id=f"leak_{seed}",
                amount=int(float(top.revenue_at_risk)) if top else 0,
            )
    else:
        allowed = None

    # Compute recovery metrics from ledger if intervention was executed
    ledger = RecoveryLedger()
    recovery_metrics: RecoveryMetrics | None = None
    if intervention_result is not None and intervention_result.executed:
        try:
            recovery_metrics = calculate_recovery_metrics(ledger)
        except Exception:
            recovery_metrics = None

    recovery_dict: dict[str, Any] | None = None
    if recovery_metrics is not None:
        recovery_dict = {
            "interventions": recovery_metrics.interventions,
            "paid_interventions": recovery_metrics.paid_interventions,
            "recovery_rate": recovery_metrics.recovery_rate,
            "recovered_revenue": str(recovery_metrics.recovered_revenue),
        }

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
        intervention={
            "action": intervention_result.action if intervention_result else None,
            "executed": intervention_result.executed if intervention_result else False,
            "reason": intervention_result.reason if intervention_result else None,
        } if intervention_result is not None else None,
        recovery=recovery_dict,
        agent_used=agent_used,
    )
