from app.pipeline import InvestigationPipeline


def test_pipeline_is_event_scoped() -> None:
    calls = []

    def investigator(event):
        calls.append(event["id"])
        return {"action": "DO_NOT_INTERVENE"}

    pipeline = InvestigationPipeline(investigator)
    outcome = pipeline.handle(
        {"event_id": "evt-1"},
        {"id": "evt-1", "status": "failed"},
    )

    assert outcome.event_id == "evt-1"
    assert outcome.status == "completed"
    assert outcome.result["action"] == "DO_NOT_INTERVENE"
    assert calls == ["evt-1"]
