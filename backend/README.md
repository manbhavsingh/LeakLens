# LeakLens — Backend

FastAPI backend for the AI revenue-leak detection pipeline.

## Current state (updated 2026-08-28)

- **Pipeline complete**: end-to-end from webhook ingestion through investigation, policy gate, intervention execution, and recovery ledger.
- **LLM agent wired**: `app/agent.py` runs bounded tool-calling loop (`max_steps=6`) with deterministic policy boundary.
- **Intervention executor**: `app/interventions.py` executes `RECOVERY_PAYMENT_LINK` via `FakePaymentProvider` (tests) / real provider (production).
- **Recovery ledger**: `app/recovery.py` tracks `InterventionRecord` statuses (`CREATED`, `PAID`, `EXPIRED`, `FAILED`) and computes `recovered_revenue()`.
- **Confidence threading**: `app/investigator.py` pulls agent `confidence` (0.55–0.95); exposed in `/api/evaluation` and `/demo/evaluate`.
- **Audit trail endpoint**: `GET /api/interventions` returns intervention records + `recovery_rate`.
- **Metrics endpoint**: `GET /metrics` exposes webhook / job / investigation counters from `app/observability.py`.
- **CORS tightened**: `allow_origins=["http://localhost:3000", "https://leaklens-demo.example.com"]` (update for your demo domain).
- **Cleaned**: removed `debug_state.json`, `repair_and_check.py`.

## Quick start

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Key endpoints (updated)

| Method | Path | Purpose |
|---|---|---|
| POST | `/demo/evaluate` | Deterministic demo (includes `confidence`, `intervention`, `recovery`) |
| GET | `/api/evaluation` | Full evaluation with confidence + recovery metrics |
| GET | `/api/interventions` | Audit trail of recovery interventions with recovery rate |
| GET | `/metrics` | Live counters (webhook_events, investigations, etc.) |
| POST | `/webhooks/razorpay` | Verified webhook → event store → job queue → investigation |
| GET | `/health` | Service health |

## Tests

```bash
cd backend
pytest -q   # 64 tests pass (verified 2026-08-28)
```

## Configuration (`.env.example`)

- `LEAKLENS_LLM_API_KEY` / `LEAKLENS_LLM_MODEL` / `LEAKLENS_LLM_BASE_URL`
- `RAZORPAY_WEBHOOK_SECRET`
- `DATABASE_URL` (PostgreSQL)

## Project layout

```
backend/
  app/
    main.py          # FastAPI app, endpoints, middleware
    agent.py         # Bounded LLM tool-calling loop
    pipeline.py      # Job queue boundary
    interventions.py # Execution + policy gate
    recovery.py      # Ledger + attribution
    e2e.py           # Evaluation pipeline (confidence wired)
    observer.py      # Metrics
  tests/             # 25 test files
  requirements.txt
```

## Hackathon notes

- Frontend is at `../frontend/` (static `index.html`). Serve on port 5173.
- All demo endpoints work without external keys (deterministic scaffold in `investigator.py`).
- For judges: show `/api/interventions` + `/metrics` to demonstrate auditability and observability.
