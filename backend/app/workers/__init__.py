from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "reverse_api_engineer",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.workers.tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=settings.CLI_TIMEOUT_SECONDS,
    task_soft_time_limit=settings.CLI_TIMEOUT_SECONDS - 60,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=10,
    result_expires=3600,
    beat_schedule={},
)

# Auto-discover tasks
celery_app.autodiscover_tasks(["app.workers"])