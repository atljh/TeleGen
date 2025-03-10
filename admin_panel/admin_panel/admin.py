from django.contrib import admin
from .models import User, Channel, Flow, Post

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("telegram_id", "username", "subscription_status", "subscription_end_date")
    search_fields = ("telegram_id", "username")
    list_filter = ("subscription_status",)

    list_display_labels = {
        "telegram_id": "Telegram ID",
        "username": "Ім'я користувача",
        "subscription_status": "Статус підписки",
        "subscription_end_date": "Дата закінчення підписки",
    }


@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    list_display = ("channel_name", "channel_id", "user", "added_at")
    search_fields = ("channel_name", "channel_id")

    list_display_labels = {
        "channel_name": "Назва каналу",
        "channel_id": "ID каналу",
        "user": "Користувач",
        "added_at": "Дата додавання",
    }


@admin.register(Flow)
class FlowAdmin(admin.ModelAdmin):
    list_display = ("name", "channel", "source_type", "created_at")
    search_fields = ("name", "source_type")

    list_display_labels = {
        "name": "Назва флоу",
        "channel": "Канал",
        "source_type": "Тип джерела",
        "created_at": "Дата створення",
    }


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("id", "flow", "status", "scheduled_time", "published_at")
    search_fields = ("flow__name", "status")

    list_display_labels = {
        "id": "ID",
        "flow": "Флоу",
        "status": "Статус",
        "scheduled_time": "Запланований час",
        "published_at": "Дата публікації",
    }