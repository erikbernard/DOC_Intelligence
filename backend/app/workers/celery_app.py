"""Celery Application configuration and Task Routing."""

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "doc_intelligence_worker",
    broker=settings.celery_broker,
    backend=settings.celery_backend,
    include=[
        "app.workers.tasks.ocr_tasks",
        "app.workers.tasks.webhook_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=120,  # 2 minutes hard limit per task
    task_soft_time_limit=90,
    worker_concurrency=2,
    task_routes={
        "app.workers.tasks.ocr_tasks.*": {"queue": "ocr"},
        "app.workers.tasks.webhook_tasks.*": {"queue": "webhooks"},
    },
)
