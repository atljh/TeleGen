# urls.py
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from payments import views as payment_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("webhook/monobank/", payment_views.monobank_webhook, name="monobank_webhook"),
    path(
        "webhook/cryptobot/", payment_views.cryptobot_webhook, name="cryptobot_webhook"
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
