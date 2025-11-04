from typing import ClassVar

from django.contrib import admin

from .models import (
    AISettings,
    Channel,
    Draft,
    Flow,
    Payment,
    Post,
    PostImage,
    PostVideo,
    PromoCode,
    Subscription,
    Tariff,
    TariffPeriod,
    User,
)


class AISettingsInline(admin.StackedInline):
    model = AISettings
    extra = 0
    max_num = 1
    can_delete = False


class SubscriptionInline(admin.TabularInline):
    model = Subscription
    extra = 0
    show_change_link = True
    fields = ("tariff_period", "is_active", "end_date")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(is_active=True)


class ChannelInline(admin.TabularInline):
    model = Channel
    extra = 0
    fields = (
        "name",
        "created_at",
    )
    readonly_fields = ("created_at",)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("telegram_id", "username", "generated_posts_count")
    readonly_fields = ("created_at",)
    fields = (
        "telegram_id",
        "username",
        "first_name",
        "last_name",
        "generated_posts_count",
        "generation_reset_at",
    )

    inlines: ClassVar[list[admin.TabularInline]] = [
        SubscriptionInline,
        ChannelInline,
    ]


@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    list_display = ("name", "channel_id", "user", "created_at", "is_active")
    search_fields = ("name", "channel_id", "user__username", "user__telegram_id")
    list_filter = ("is_active", "created_at")
    readonly_fields = ("created_at",)


@admin.register(Flow)
class FlowAdmin(admin.ModelAdmin):
    list_display = ("name", "frequency", "next_generation_time")
    list_filter = ("frequency",)
    search_fields = ("name", "theme", "channel__name", "channel__channel_id")
    readonly_fields = ("created_at", "next_generation_time")

    inlines: ClassVar[list[admin.TabularInline]] = [AISettingsInline]


class PostImageInline(admin.TabularInline):
    model = PostImage
    extra = 1


class PostVideoInline(admin.TabularInline):
    model = PostVideo
    extra = 1


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        "flow",
        "original_link",
        "source_url",
        "publication_date",
        "status",
        "created_at",
    )
    readonly_fields = ("created_at",)
    search_fields = (
        "content",
        "source_url",
        "flow__name",
        "original_link",
        "flow__channel__name",
    )
    list_filter = ("status", "created_at")
    inlines: ClassVar[list[admin.TabularInline]] = [PostImageInline, PostVideoInline]


@admin.register(Draft)
class DraftAdmin(admin.ModelAdmin):
    list_display = ("user", "post", "created_at")
    search_fields = ("user__username", "post__content")
    list_filter = ("created_at",)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("user", "amount", "payment_method", "payment_date", "is_successful")
    search_fields = ("user__username", "payment_method")
    list_filter = ("is_successful", "payment_date")


@admin.register(AISettings)
class AISettingsAdmin(admin.ModelAdmin):
    list_display = ("flow", "style", "created_at")
    search_fields = ("style",)
    list_filter = ("style", "created_at")


@admin.register(Tariff)
class TariffAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name", "description")


@admin.register(TariffPeriod)
class TariffPeriodAdmin(admin.ModelAdmin):
    list_display = ("tariff", "months", "price")
    list_filter = ("tariff", "months")
    search_fields = ("tariff__name",)
    ordering = ("tariff", "months")


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ("code", "tariff", "months", "discount_percent", "is_active", "created_at")
    list_filter = ("is_active", "tariff", "months")
    search_fields = ("code", "tariff__name")
    ordering = ("-created_at",)
    fields = ("code", "tariff", "months", "discount_percent", "is_active", "created_at")
    readonly_fields = ("created_at",)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "tariff_period",
        "start_date",
        "end_date",
        "is_active",
    )
    list_filter = ("is_active", "tariff_period__tariff")
    search_fields = ("user__username", "channel__name", "tariff_period__tariff__name")
    ordering = ("-start_date",)
