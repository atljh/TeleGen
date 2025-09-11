import os

import django
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.prod")

if not settings.configured:
    django.setup()


from admin_panel.admin_panel.models import Channel, Flow, Post, User
