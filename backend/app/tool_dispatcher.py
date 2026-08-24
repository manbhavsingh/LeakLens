from __future__ import annotations

from datetime import datetime
from typing import Any, Iterable

from .analysis_tools import calculate_revenue_impact, compare_time_windows, get_customer_history
from .leak_tools import find_revenue_leaks, get_payment_failure_breakdown
from .models import Transaction


class ToolExecutionError(ValueError):
    pass


class InvestigatorToolDispatcher:
    """Executes only explicitly allowlisted read-only investigator tools."""

    def __init__(self, transactions: Iterable[Transaction]):
        self._transactions = list(transactions)

    def execute(self, name: str, arguments: dict[str, Any]) -> dict[str, Any] | list[dict[str, Any]]:
        if name == "find_revenue_leaks":
            return find_revenue_leaks(self._transactions)
        if name == "get_payment_failure_breakdown":
            return get_payment_failure_breakdown(
                self._transactions,
                payment_method=arguments.get("payment_method"),
            )
        if name == "get_customer_history":
            customer_id = arguments.get("customer_id")
            if not customer_id:
                raise ToolExecutionError("customer_id is required")
            return get_customer_history(self._transactions, customer_id)
        if name == "compare_time_windows":
            try:
                start = datetime.fromisoformat(arguments["start"])
                split = datetime.fromisoformat(arguments["split"])
                end = datetime.fromisoformat(arguments["end"])
            except (KeyError, ValueError) as exc:
                raise ToolExecutionError("start, split and end must be ISO timestamps") from exc
            return compare_time_windows(self._transactions, start=start, split=split, end=end)
        if name == "calculate_revenue_impact":
            expected_conversion = float(arguments.get("expected_conversion", 0))
            if not 0 <= expected_conversion <= 1:
                raise ToolExecutionError("expected_conversion must be between 0 and 1")
            return calculate_revenue_impact(
                self._transactions,
                expected_conversion=expected_conversion,
            )
        raise ToolExecutionError(f"Unknown investigator tool: {name}")
