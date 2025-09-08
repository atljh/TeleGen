import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "admin_panel.core.settings")

app = Celery("bot")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)
