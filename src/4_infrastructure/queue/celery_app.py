"""Celery application configuration."""
from celery import Celery
from src.config import settings

# Create Celery instance
celery_app = Celery(
    "study_assistant",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "src.4_infrastructure.queue.tasks.lecture_processing"
    ]
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes max
    task_soft_time_limit=25 * 60,  # 25 minutes soft limit
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Task routes
celery_app.conf.task_routes = {
    'src.4_infrastructure.queue.tasks.lecture_processing.*': {'queue': 'lecture_processing'},
}
