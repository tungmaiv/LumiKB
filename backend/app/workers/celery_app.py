"""Celery application configuration for document processing workers."""

from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

# Create Celery application
celery_app = Celery(
    "lumikb",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

# Celery configuration
celery_app.conf.update(
    # Task routing - route document processing to dedicated queue
    task_routes={
        "app.workers.document_tasks.*": {"queue": "document_processing"},
        "app.workers.outbox_tasks.*": {"queue": "default"},
    },
    # Queue configuration
    task_queues={
        "default": {},
        "document_processing": {},
    },
    # Default queue for tasks without explicit routing
    task_default_queue="default",
    # Task serialization
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    # Timezone
    timezone="UTC",
    enable_utc=True,
    # Task execution settings
    task_acks_late=True,  # Acknowledge after task completes (not when received)
    task_reject_on_worker_lost=True,  # Requeue if worker dies
    worker_prefetch_multiplier=1,  # Only fetch one task at a time per worker
    # Visibility timeout for document processing (10 minutes)
    broker_transport_options={
        "visibility_timeout": settings.document_processing_timeout,
    },
    # Result backend settings
    result_expires=3600,  # Results expire after 1 hour
    # Task time limits
    task_soft_time_limit=540,  # 9 minutes soft limit
    task_time_limit=600,  # 10 minutes hard limit
    # Beat schedule for periodic tasks
    beat_schedule={
        "process-outbox-events": {
            "task": "app.workers.outbox_tasks.process_outbox_events",
            "schedule": 10.0,  # Every 10 seconds
        },
        "reconcile-data-consistency": {
            "task": "app.workers.outbox_tasks.reconcile_data_consistency",
            "schedule": 3600.0,  # Every hour (3600 seconds)
        },
        "cleanup-processed-outbox-events": {
            "task": "app.workers.outbox_tasks.cleanup_processed_outbox_events",
            # Daily at 3 AM UTC
            "schedule": crontab(hour=3, minute=0),
        },
    },
)

# Auto-discover tasks in worker modules
celery_app.autodiscover_tasks(
    [
        "app.workers.outbox_tasks",
        "app.workers.document_tasks",
    ]
)
