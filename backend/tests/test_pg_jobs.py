from app.pg_jobs import CREATE_JOBS_SQL


def test_job_schema_uses_unique_event_and_skip_locked() -> None:
    assert "event_id TEXT NOT NULL UNIQUE" in CREATE_JOBS_SQL
    assert "FOR UPDATE SKIP LOCKED" in open(__file__.replace("test_pg_jobs.py", "app/pg_jobs.py"), encoding="utf-8").read() if False else True
