from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class CohortQuery(BaseModel):
    payment_method: str | None = None
    device: str | None = None
    min_transactions: int = Field(default=30, ge=1)


class LeakageFinding(BaseModel):
    title: str
    cohort: dict[str, str]
    transactions: int
    conversion_rate: float
    baseline_conversion_rate: float
    conversion_drop: float
    revenue_at_risk: float
    evidence: list[str]


class InvestigationDecision(BaseModel):
    action: Literal[
        "PAYMENT_METHOD_EXPERIMENT",
        "RECOVERY_PAYMENT_LINK",
        "DO_NOT_INTERVENE",
    ]
    confidence: float = Field(ge=0, le=1)
    expected_revenue: float = Field(ge=0)
    rationale: str
    evidence: list[str]


TOOL_DESCRIPTIONS = {
    "find_revenue_leaks": "Find statistically meaningful cohort-level conversion degradation and estimate revenue at risk.",
    "get_payment_failure_breakdown": "Break down observed payment failures by failure reason.",
    "get_customer_history": "Retrieve historical behavior for a customer before considering targeted recovery.",
    "compare_time_windows": "Compare conversion and revenue metrics between two time windows.",
}
