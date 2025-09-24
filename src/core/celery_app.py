import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.prod")

app = Celery("TeleGen")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks(["bot"])

__all__ = ("app",)
