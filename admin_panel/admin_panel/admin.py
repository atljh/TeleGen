from django.contrib import admin
from .models import (
    User, Channel, Flow, Post, Draft, Subscription, Payment, AISettings, Statistics, PostImage
)


class AISettingsInline(admin.StackedInline):
    model = AISettings
    extra = 0
    max_num = 1
    can_delete = False

class SubscriptionInline(admin.TabularInline):
    model = Subscription
    extra = 0
    fields = ('channel', 'subscription_type', 'end_date', 'is_active')

class ChannelInline(admin.TabularInline):
    model = Channel
    extra = 0
    fields = ('name', 'created_at',)
    readonly_fields = ('created_at',)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("telegram_id", "username", "subscription_status",)
    readonly_fields = ("created_at", )
    fields = ("telegram_id", "username", "first_name", "last_name",
              "subscription_status", "subscription_end_date", "subscription_type",
              "payment_method",)

    inlines = [ChannelInline, SubscriptionInline]


@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    list_display = ('name', 'channel_id', 'user', 'created_at', 'is_active')
    search_fields = ('name', 'channel_id', 'user__username', 'user__telegram_id')
    list_filter = ('is_active', 'created_at')
    readonly_fields = ('created_at',)

@admin.register(Flow)
class FlowAdmin(admin.ModelAdmin):
    list_display = ('name', 'frequency', 'next_generation_time')
    list_filter = ('frequency',)
    search_fields = ('name', 'theme')

    inlines = [AISettingsInline]

class PostImageInline(admin.TabularInline):
    model = PostImage
    extra = 1

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('flow', 'publication_date', 'is_published', 'is_draft', 'created_at')
    search_fields = ('content', 'source_url')
    list_filter = ('is_published', 'is_draft', 'created_at')
    inlines = [PostImageInline]

@admin.register(Draft)
class DraftAdmin(admin.ModelAdmin):
    list_display = ('user', 'post', 'created_at')
    search_fields = ('user__username', 'post__content')
    list_filter = ('created_at',)

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'channel', 'subscription_type', 'start_date', 'end_date', 'is_active')
    search_fields = ('user__username', 'channel__name')
    list_filter = ('subscription_type', 'is_active')

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'payment_method', 'payment_date', 'is_successful')
    search_fields = ('user__username', 'payment_method')
    list_filter = ('is_successful', 'payment_date')

@admin.register(AISettings)
class AISettingsAdmin(admin.ModelAdmin):
    list_display = ('flow', 'style', 'created_at')
    search_fields = ('style',)
    list_filter = ('style', 'created_at')

# @admin.register(Statistics)
# class StatisticsAdmin(admin.ModelAdmin):
#     list_display = ('user', 'channel', 'total_posts', 'total_views', 'total_likes', 'last_updated')
#     search_fields = ('user__username', 'channel__name')
#     list_filter = ('last_updated',)

