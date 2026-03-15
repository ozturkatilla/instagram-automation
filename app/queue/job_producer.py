from rq import Queue
from app.queue.redis_client import get_redis_connection
from app.queue.tasks import task_send_direct, task_get_likers
from app.core.config import get_settings

settings = get_settings()


def get_queue() -> Queue:
    redis = get_redis_connection()
    return Queue(settings.JOB_QUEUE_NAME, connection=redis)


def enqueue_send_direct(username: str, user_ids: list, message: str, delay: float = 3.0):
    q = get_queue()
    job = q.enqueue(
        task_send_direct,
        username, user_ids, message, delay,
        job_timeout=3600,
    )
    return {"job_id": job.id, "status": "queued"}


def enqueue_get_likers(username: str, media_id: str):
    q = get_queue()
    job = q.enqueue(task_get_likers, username, media_id)
    return {"job_id": job.id, "status": "queued"}