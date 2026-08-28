# LeakLens Dashboard

The dashboard is a dependency-light static frontend for the local FastAPI demo.

Run the backend on `http://localhost:8000`, then serve this directory with any static HTTP server.

Example:

```bash
python -m http.server 5173
```

Open `http://localhost:5173` and click **Run demo investigation**.

The dashboard expects:
- `POST http://localhost:8000/demo/evaluate`
- `GET  http://localhost:8000/api/evaluation` (for `confidence`, `intervention`, `recovery`)
- `GET  http://localhost:8000/api/interventions` (audit trail + `recovery_rate`)
- `GET  http://localhost:8000/metrics` (live counters)
