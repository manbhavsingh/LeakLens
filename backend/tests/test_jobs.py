from app.jobs import JobQueue, JobStatus


def test_duplicate_event_creates_one_job() -> None:
    queue = JobQueue()
    first = queue.enqueue(event_id="evt-1", job_type="investigate")
    second = queue.enqueue(event_id="evt-1", job_type="investigate")

    assert first.id == second.id
    assert len(queue.jobs) == 1


def test_failed_job_retries_then_succeeds() -> None:
    queue = JobQueue()
    job = queue.enqueue(event_id="evt-2", job_type="investigate")
    attempts = {"count": 0}

    def handler(_job):
        attempts["count"] += 1
        if attempts["count"] < 2:
            raise RuntimeError("temporary failure")

    first = queue.run(job.id, handler)
    assert first.status is JobStatus.PENDING
    assert first.attempts == 1

    second = queue.run(job.id, handler)
    assert second.status is JobStatus.SUCCEEDED
    assert second.attempts == 2
