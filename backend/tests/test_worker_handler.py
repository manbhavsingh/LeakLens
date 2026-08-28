from app.worker_handler import InvestigationJobHandler


class PolicyMock:
    allowed = True
    action = "DO_NOT_INTERVENE"
    reason = "No intervention needed."


class FakeAgent:
    class Result:
        decision = {
            "hypothesis": "insufficient evidence",
            "confidence": 0.9,
            "action": "DO_NOT_INTERVENE",
            "expected_revenue": 0,
            "rationale": "observe only",
            "evidence": [],
        }
        policy = PolicyMock()
        trace = ({"type": "decision"},)

    def investigate(self, _finding):
        return self.Result()


class FakeStore:
    def __init__(self):
        self.saved = []

    def save_once(self, **kwargs):
        self.saved.append(kwargs)
        return True


def test_handler_persists_agent_decision() -> None:
    store = FakeStore()
    handler = InvestigationJobHandler(FakeAgent(), store)

    result = handler(
        {"event_id": "evt-1"},
        lambda event_id: {"event_id": event_id, "event_type": "payment.failed", "status": "failed"},
    )

    assert result["decision"]["action"] == "DO_NOT_INTERVENE"
    assert store.saved[0]["event_id"] == "evt-1"
    assert store.saved[0]["status"] == "completed"
