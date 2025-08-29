import os
import django
from django.conf import settings

DJANGO_SETTINGS_MODULE = "admin_panel.core.settings"

if not settings.configured:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", DJANGO_SETTINGS_MODULE)
    django.setup()

from admin_panel.admin_panel.models import User, Channel, Flow, Post

from .user_service import UserService
from .channel_service import ChannelService
from .flow_service import FlowService
from .post_service import PostService
from .aisettings_service import AISettingsService
from .subscription_service import SubscriptionService
from .payment_service import PaymentService
from .statistics_service import StatisticsService
from .userbot_service import UserbotService, EnhancedUserbotService

from .web.web_service import WebService
from .web.rss_service import RssService
from .web.cloudflare_bypass_service import CloudflareBypass
from .web.web_scraper_service import WebScraperService
from .web.image_extractor_service import ImageExtractorService
from .web.post_builder_service import PostBuilderService
from .web.content_processor_service import ContentProcessorService

__all__ = [
    'WebService',
    'UserService',
    'ChannelService',
    'FlowService',
    'PostService',
    'AISettingsService',
    'SubscriptionService',
    'PaymentService',
    'StatisticsService',
    'UserbotService',
    'EnhancedUserbotService',
    'RssService',
    'CloudflareBypass',
    'WebScraperService',
    'ImageExtractorService',
    'PostBuilderService',
    'ContentProcessorService'
]