"""Celery application configuration."""
from celery import Celery
from src.config import settings

from src.infrastructure.database.models.user import UserModel
from src.infrastructure.database.models.course import CourseModel
from src.infrastructure.database.models.lecture import LectureModel
from src.infrastructure.database.models.test import TestModel
from src.infrastructure.database.models.student_attempt import StudentAttemptModel
from src.infrastructure.database.models.embedding import LectureEmbedding

celery_app = Celery(
    "study_assistant",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "src.infrastructure.queue.tasks.lecture_processing"
    ]
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,
    task_soft_time_limit=25 * 60,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

celery_app.conf.task_routes = {
    'src.infrastructure.queue.tasks.lecture_processing.*': {'queue': 'lecture_processing'},
}
