from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .detector import LeakCandidate, detect_cohort_leaks
from .leak_tools import get_payment_failure_breakdown
from .models import Transaction


@dataclass(frozen=True)
class Investigation:
    finding: LeakCandidate
    failure_breakdown: dict[str, int]
    hypothesis: str
    confidence: float
    recommended_action: str
    evidence: tuple[str, ...]


def investigate(transactions: Iterable[Transaction]) -> list[Investigation]:
    """Run an auditable investigation without an LLM.

    This is the deterministic scaffold the eventual tool-calling LLM will use.
    It forces every recommendation to be backed by observable evidence first.
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

        if timeout_count > 0 and finding.conversion_drop >= 0.20:
            hypothesis = (
                f"The {method.upper()} cohort shows a substantial conversion degradation; "
                "timeout failures are a plausible contributor and should be tested before causal claims are made."
            )
            confidence = min(0.95, 0.60 + finding.conversion_drop)
            action = "PAYMENT_METHOD_EXPERIMENT"
        else:
            hypothesis = (
                f"The {method.upper()} cohort is underperforming its complementary population, "
                "but the available evidence is insufficient for a strong intervention."
            )
            confidence = 0.55
            action = "DO_NOT_INTERVENE"

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
