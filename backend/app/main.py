from fastapi import FastAPI

from .e2e import run_evaluation

app = FastAPI(
    title="LeakLens API",
    version="0.1.0",
    description="AI revenue leakage investigation and recovery platform.",
)


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
