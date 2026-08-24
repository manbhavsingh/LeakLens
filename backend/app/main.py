import os
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from .e2e import run_evaluation
from .event_store import EventStore
from .health import router as health_router
from .observability import metrics
from .razorpay import WebhookVerificationError, parse_payment_webhook

app = FastAPI(
    title="LeakLens API",
    version="0.1.0",
    description="AI revenue leakage investigation and recovery platform.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
event_store = EventStore()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "leaklens-api"}


@app.post("/demo/evaluate")
def demo_evaluate() -> dict:
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
        event = parse_payment_webhook(body, x_razorpay_event_id, x_razorpay_signature, secret)
    except WebhookVerificationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    metrics.webhook_events += 1
    accepted = event_store.add_if_new(event)
    if not accepted:
        metrics.duplicate_events += 1
    return {"accepted": accepted, "event_id": event.event_id, "event_type": event.event_type}


@app.get("/")
def dashboard() -> FileResponse:
    frontend = Path(__file__).resolve().parents[2] / "frontend" / "index.html"
    if not frontend.exists():
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return FileResponse(frontend)
