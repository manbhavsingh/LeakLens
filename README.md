# LeakLens

**AI Revenue Leakage Investigator for payment systems**

LeakLens detects cohort-level payment conversion degradation, investigates it with evidence-gathering tools, applies a bounded policy gate, and tracks whether an intervention actually recovered revenue.

## Why it is different

LeakLens is not an LLM dashboard that summarizes payment data. The model operates inside a bounded investigation loop: it must gather evidence through explicit read-only tools, produce a structured hypothesis and recommendation, and pass a deterministic policy gate before an intervention can execute.

## Architecture

```text
Razorpay webhook
      |
      v
Signature verification
      |
      v
PostgreSQL event store
      |
      v
PostgreSQL job queue (FOR UPDATE SKIP LOCKED)
      |
      v
Worker pool
      |
      v
Leak detector + AI investigator
      |
      +----> read-only analytics tools
      |
      v
Policy gate
      |
      v
Intervention executor
      |
      v
Razorpay Payment Link / experiment
      |
      v
Webhook outcome
      |
      v
Recovery ledger + revenue metrics
```

## Safety and reliability

- Webhook signatures are verified before ingestion.
- Event IDs are idempotent.
- Jobs are claimed with PostgreSQL `FOR UPDATE SKIP LOCKED`.
- Stale jobs can be reclaimed after worker failure.
- Interventions are allowlisted and confidence-gated (policy gate in `app/policy.py`).
- Recovery attribution uses an explicit intervention reference ID.
- Tests use a fake payment provider; credentials are never committed.

## Local demo

### Backend

Configure variables from `backend/.env.example`, then run FastAPI on port 8000:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

The deterministic demo endpoint is:

```text
POST /demo/evaluate
GET  /api/evaluation        # full eval: confidence, intervention, recovery
GET  /api/interventions     # audit trail + recovery_rate
GET  /metrics               # live counters (webhook, jobs, interventions)
```

### Dashboard

```bash
cd frontend
python -m http.server 5173
```

Open `http://localhost:5173` and click **Run demo investigation**.

### Testing

```bash
cd backend
pytest -q   # 64 tests (verified 2026-08-28)
```

CI runs the backend test suite on pushes and pull requests.

## Evaluation model

The deterministic demo uses synthetic transactions and an injected leak so the detection pipeline can be evaluated reproducibly. Razorpay and LLM credentials are runtime configuration and are not required for the unit-test suite.

The evaluation pipeline exposes a `confidence` score (0.55–0.95) representing how strongly the evidence supports an intervention, alongside the policy gate decision, intervention outcome, and recovery attribution — giving judges a complete view of every decision the system made.
