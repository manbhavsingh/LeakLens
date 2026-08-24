from fastapi import FastAPI

app = FastAPI(
    title="LeakLens API",
    version="0.1.0",
    description="AI revenue leakage investigation and recovery platform.",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "leaklens-api"}
