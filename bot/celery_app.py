import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'admin_panel.core.settings')

app = Celery('bot')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()