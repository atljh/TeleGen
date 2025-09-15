import os

import django
from django.conf import settings

from .aisettings_service import AISettingsService
from .channel_service import ChannelService
from .flow_service import FlowService
from .payment_service import PaymentService
from .post import PostService
from .statistics_service import StatisticsService
from .subscription_service import SubscriptionService
from .telegram_userbot import EnhancedUserbotService
from .user_service import UserService
from .web.cloudflare_bypass_service import CloudflareBypass
from .web.content_processor_service import ContentProcessorService
from .web.image_extractor_service import ImageExtractorService
from .web.post_builder_service import PostBuilderService
from .web.rss_service import RssService
from .web.web_scraper_service import WebScraperService
from .web.web_service import WebService

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.prod")

if not settings.configured:
    django.setup()

__all__ = [
    "AISettingsService",
    "ChannelService",
    "CloudflareBypass",
    "ContentProcessorService",
    "EnhancedUserbotService",
    "FlowService",
    "ImageExtractorService",
    "PaymentService",
    "PostBuilderService",
    "PostService",
    "RssService",
    "StatisticsService",
    "SubscriptionService",
    "UserService",
    "WebScraperService",
    "WebService",
]
