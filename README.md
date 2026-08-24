# LeakLens

**AI Revenue Recovery Scientist**

LeakLens discovers where merchant revenue is leaking, investigates the evidence, forms testable hypotheses, proposes bounded interventions, and measures whether those interventions recover incremental revenue.

## Current milestone

Phase 1 implementation: deterministic analytics foundation and synthetic merchant universe.

The system deliberately keeps the analytics layer deterministic before adding an LLM investigator. This gives the agent auditable tools and an objective evaluation environment.

## Architecture

```text
Synthetic / Razorpay Events
          |
          v
     Event Ingestion
          |
          v
   PostgreSQL Event Store
          |
          v
 Deterministic Analytics
          |
          v
    AI Investigator
          |
          v
 Policy / Safety Gate
          |
          v
     Intervention
          |
          v
  Experiment + Measurement
```

## Development

The first milestone uses Python, FastAPI, SQLAlchemy, PostgreSQL, and pytest.

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

See `docs/architecture.md` for the current design contract.
