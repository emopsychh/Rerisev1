import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("rerise")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "sync-pending-payments-every-5-min": {
        "task": "apps.commerce.tasks.sync_pending_payments",
        "schedule": crontab(minute="*/5"),
    },
}
