"""
@file: celery_app.py
@description: Celery app - Redis broker, queues: publish, notifications, analytics.
@dependencies: celery, redis
@created: 2025-02-19
"""

import os

from celery import Celery

broker = os.getenv("REDIS_URL", "redis://localhost:6379/0")
app = Celery(
    "lytslot",
    broker=broker,
    backend=broker,
    include=["services.worker.tasks"],
)
app.conf.task_routes = {
    "services.worker.tasks.ping": {"queue": "default"},
    "services.worker.tasks.publish_order": {"queue": "publish"},
    "services.worker.tasks.send_notification": {"queue": "notifications"},
    "services.worker.tasks.notify_new_order": {"queue": "notifications"},
    "services.worker.tasks.notify_order_cancelled": {"queue": "notifications"},
    "services.worker.tasks.notify_payment_received": {"queue": "notifications"},
    "services.worker.tasks.process_webhook": {"queue": "notifications"},
    "services.worker.tasks.aggregate_analytics": {"queue": "analytics"},
}
app.conf.task_serializer = "json"
app.conf.result_serializer = "json"
app.conf.timezone = "UTC"
app.conf.enable_utc = True
app.conf.task_default_queue = "default"
