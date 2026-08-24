import os

from fastapi import FastAPI, Header, HTTPException, Request

from .e2e import run_evaluation
from .event_store import EventStore
from .razorpay import WebhookVerificationError, parse_payment_webhook

app = FastAPI(
    title="LeakLens API",
    version="0.1.0",
    description="AI revenue leakage investigation and recovery platform.",
)

event_store = EventStore()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "leaklens-api"}


@app.post("/demo/evaluate")
def demo_evaluate() -> dict:
    """Run the reproducible deterministic demo pipeline."""
    result = run_evaluation()
    return {
        "transaction_count": result.transaction_count,
        "injected_leak": result.injected_leak,
        "ground_truth_revenue_at_risk": str(result.ground_truth_revenue_at_risk),
        "detected_findings": result.detected_findings,
        "top_finding": result.top_finding,
        "hypothesis": result.hypothesis,
        "recommended_action": result.recommended_action,
        "policy_allowed": result.policy_allowed,
    }


@app.post("/webhooks/razorpay")
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: str = Header(default=""),
    x_razorpay_event_id: str = Header(default=""),
) -> dict[str, object]:
    secret = os.getenv("RAZORPAY_WEBHOOK_SECRET")
    if not secret:
        raise HTTPException(status_code=503, detail="RAZORPAY_WEBHOOK_SECRET is not configured")
    if not x_razorpay_event_id:
        raise HTTPException(status_code=400, detail="Missing x-razorpay-event-id")

    body = await request.body()
    try:
        event = parse_payment_webhook(
            body,
            x_razorpay_event_id,
            x_razorpay_signature,
            secret,
        )
    except WebhookVerificationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    accepted = event_store.add_if_new(event)
    return {"accepted": accepted, "event_id": event.event_id, "event_type": event.event_type}
