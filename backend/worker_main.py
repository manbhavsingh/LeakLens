from app.jobs import JobQueue
from app.worker import InvestigationWorker


def build_worker(queue: JobQueue, handler):
    return InvestigationWorker(queue, handler)


if __name__ == "__main__":
    print("LeakLens worker entrypoint ready; attach a durable queue and handler.")
