import os

import django
from django.conf import settings

DJANGO_SETTINGS_MODULE = "admin_panel.core.settings"

if not settings.configured:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", DJANGO_SETTINGS_MODULE)
    django.setup()

from admin_panel.admin_panel.models import Channel, Flow, Post, User
