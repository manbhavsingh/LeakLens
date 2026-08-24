from datetime import timezone

import pytest

from app.synthetic import generate_transactions
from app.tool_dispatcher import InvestigatorToolDispatcher, ToolExecutionError


def test_dispatcher_executes_read_only_tools() -> None:
    rows = generate_transactions(count=1000, seed=42)
    dispatcher = InvestigatorToolDispatcher(rows)

    findings = dispatcher.execute("find_revenue_leaks", {})
    assert isinstance(findings, list)

    breakdown = dispatcher.execute("get_payment_failure_breakdown", {"payment_method": "upi"})
    assert isinstance(breakdown, dict)


def test_dispatcher_rejects_unknown_tool() -> None:
    dispatcher = InvestigatorToolDispatcher(generate_transactions(count=20))
    with pytest.raises(ToolExecutionError):
        dispatcher.execute("delete_transactions", {})


def test_dispatcher_validates_customer_argument() -> None:
    dispatcher = InvestigatorToolDispatcher(generate_transactions(count=20))
    with pytest.raises(ToolExecutionError):
        dispatcher.execute("get_customer_history", {})
