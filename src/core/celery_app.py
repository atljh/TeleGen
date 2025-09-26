import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.prod")

app = Celery("TeleGen")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks(["bot"])

app.conf.update(
    task_always_eager=False,
    task_eager_propagates=False,
    worker_pool="solo",
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

__all__ = ("app",)
