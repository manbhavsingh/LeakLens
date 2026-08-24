from app.jobs import JobQueue, JobStatus
from app.worker import InvestigationWorker


def test_duplicate_event_does_not_duplicate_job() -> None:
    queue = JobQueue()
    a = queue.enqueue(event_id="evt-chaos", job_type="investigate")
    b = queue.enqueue(event_id="evt-chaos", job_type="investigate")
    assert a.id == b.id
    assert len(queue.jobs) == 1


def test_worker_stops_after_max_attempts() -> None:
    queue = JobQueue()
    job = queue.enqueue(event_id="evt-fail", job_type="investigate")

    def always_fails(_job):
        raise RuntimeError("downstream unavailable")

    worker = InvestigationWorker(queue, always_fails)
    worker.run_until_empty(max_cycles=10)
    assert job.status is JobStatus.FAILED
    assert job.attempts == job.max_attempts
