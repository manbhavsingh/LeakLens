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
from .recovery import RecoveryLedger
from .recovery_webhook import process_payment_event

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
recovery_ledger = RecoveryLedger()


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
        "confidence": result.confidence,
    }


@app.get("/api/evaluation")
def get_evaluation() -> dict:
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
        "intervention": result.intervention,
        "recovery": result.recovery,
        "confidence": result.confidence,
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

    try:
        result = process_payment_event(event, recovery_ledger)
    except Exception:
        result = False

    metrics.webhook_events += 1
    accepted = event_store.add_if_new(event)
    if not accepted:
        metrics.duplicate_events += 1

    from .pipeline import enqueue_memory_job
    from .jobs import JobQueue
    job_queue = JobQueue()
    enqueue_memory_job(job_queue, event.event_id)

    return {"accepted": accepted, "event_id": event.event_id, "event_type": event.event_type, "recovery_processed": result, "job_queued": job_queue.event_to_job.get(event.event_id) is not None}


@app.get("/metrics")
def get_metrics() -> dict:
    return {
        "webhook_events": metrics.webhook_events,
        "duplicate_events": metrics.duplicate_events,
        "jobs_succeeded": metrics.jobs_succeeded,
        "investigations": metrics.investigations,
        "interventions_allowed": metrics.interventions_allowed,
        "interventions_blocked": metrics.interventions_blocked,
    }


@app.get("/api/interventions")
def list_interventions() -> dict:
    """Audit trail: every recovery intervention the ledger has tracked."""
    records = []
    for r in recovery_ledger.records.values():
        records.append({
            "reference_id": r.reference_id,
            "customer_id": r.customer_id,
            "amount": str(r.amount),
            "status": r.status,
            "paid_amount": str(r.paid_amount),
            "payment_id": r.payment_id,
        })
    recovered = recovery_ledger.recovered_revenue()
    total_attempted = sum((r.amount for r in recovery_ledger.records.values()), recovered.__class__("0"))
    rate = (recovered / total_attempted) if total_attempted > 0 else 0.0
    return {
        "intervention_count": len(records),
        "recovered_revenue": str(recovered),
        "recovery_rate": float(rate),
        "records": records,
    }


@app.post("/demo/simulate-webhook")
def simulate_webhook() -> dict:
    """Run a real, signed Razorpay webhook through the entire pipeline and
    report the live state for the frontend demo."""
    from .demo_runner import run_live_simulation
    return run_live_simulation(recovery_ledger=recovery_ledger, event_store=event_store)


@app.get("/demo/live-state")
def live_state() -> dict:
    """Snapshot of recent pipeline activity (events, jobs, recovery)."""
    recovered = recovery_ledger.recovered_revenue()
    total_attempted = sum((r.amount for r in recovery_ledger.records.values()), recovered.__class__("0"))
    rate = float(recovered / total_attempted) if total_attempted > 0 else 0.0
    return {
        "events_received": event_store.count(),
        "interventions": len(recovery_ledger.records),
        "paid_interventions": sum(1 for r in recovery_ledger.records.values() if str(r.status) == "paid"),
        "recovered_revenue": str(recovered),
        "recovery_rate": rate,
    }


@app.get("/")
def dashboard() -> FileResponse:
    frontend = Path(__file__).resolve().parents[2] / "frontend" / "index.html"
    if not frontend.exists():
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return FileResponse(frontend)
