from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .detector import LeakCandidate, detect_cohort_leaks
from .leak_tools import get_payment_failure_breakdown
from .agent import LLMClient, LeakLensAgent
from .models import Transaction


@dataclass(frozen=True)
class Investigation:
    finding: LeakCandidate
    failure_breakdown: dict[str, int]
    hypothesis: str
    confidence: float
    recommended_action: str
    evidence: tuple[str, ...]


def investigate(
    transactions: Iterable[Transaction],
    llm: LLMClient | None = None,
) -> list[Investigation]:
    """Run an auditable investigation with optional LLM-driven decisions.

    When ``llm`` is provided the LeakLens agent drives the decision, still
    gated by the bounded policy. Otherwise a deterministic scaffold produces a
    defensible fallback so the demo never depends on external credentials.
    """
    rows = list(transactions)
    findings = detect_cohort_leaks(rows)
    investigations: list[Investigation] = []

    for finding in findings:
        method = finding.cohort["payment_method"]
        breakdown = get_payment_failure_breakdown(rows, payment_method=method)
        timeout_count = breakdown.get("timeout", 0)

        evidence = list(finding.evidence)
        evidence.append(f"{method.upper()} timeout failures in full population: {timeout_count}.")

        if llm is not None:
            try:
                agent = LeakLensAgent(llm, rows)
                finding_payload = {
                    "title": finding.title,
                    "cohort": finding.cohort,
                    "conversion_drop": finding.conversion_drop,
                    "revenue_at_risk": str(finding.revenue_at_risk),
                }
                agent_result = agent.run(finding_payload)
                decision = agent_result.decision
                hypothesis = str(decision.get("hypothesis", ""))
                confidence = float(decision.get("confidence", 0.55))
                action = str(decision.get("action", "DO_NOT_INTERVENE"))
                for note in decision.get("evidence", []) or []:
                    evidence.append(str(note))
            except Exception:
                hypothesis, confidence, action = _deterministic_decision(
                    method, timeout_count, finding.conversion_drop
                )
        else:
            hypothesis, confidence, action = _deterministic_decision(
                method, timeout_count, finding.conversion_drop
            )

        investigations.append(
            Investigation(
                finding=finding,
                failure_breakdown=breakdown,
                hypothesis=hypothesis,
                confidence=confidence,
                recommended_action=action,
                evidence=tuple(evidence),
            )
        )

    return investigations


def _deterministic_decision(
    method: str, timeout_count: int, conversion_drop: float
) -> tuple[str, float, str]:
    if timeout_count > 0 and conversion_drop >= 0.20:
        hypothesis = (
            f"The {method.upper()} cohort shows a substantial conversion degradation; "
            "timeout failures are a plausible contributor and should be tested before causal claims are made."
        )
        confidence = min(0.95, 0.60 + conversion_drop)
        action = "PAYMENT_METHOD_EXPERIMENT"
    else:
        hypothesis = (
            f"The {method.upper()} cohort is underperforming its complementary population, "
            "but the available evidence is insufficient for a strong intervention."
        )
        confidence = 0.55
        action = "DO_NOT_INTERVENE"
    return hypothesis, confidence, action
