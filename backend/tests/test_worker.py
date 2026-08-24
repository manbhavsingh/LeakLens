from app.jobs import JobStatus, JobQueue
from app.worker import InvestigationWorker


def test_worker_retries_and_drains_queue() -> None:
    queue = JobQueue()
    job = queue.enqueue(event_id="evt-worker", job_type="investigate")
    state = {"attempts": 0}

    def handler(_job):
        state["attempts"] += 1
        if state["attempts"] == 1:
            raise RuntimeError("temporary downstream failure")

    worker = InvestigationWorker(queue, handler)
    assert worker.run_until_empty(max_cycles=5) == 2
    assert job.status is JobStatus.SUCCEEDED
    assert job.attempts == 2
