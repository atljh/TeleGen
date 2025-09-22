# urls.py
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

from admin_panel import cryptobot_webhook, monobank_webhook

urlpatterns = [
    path("admin/", admin.site.urls),
    path("webhook/monobank/", monobank_webhook, name="monobank_webhook"),
    path("webhook/cryptobot/", cryptobot_webhook, name="cryptobot_webhook"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
