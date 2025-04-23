import os
import django
from django.conf import settings

DJANGO_SETTINGS_MODULE = "admin_panel.core.settings"

if not settings.configured:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", DJANGO_SETTINGS_MODULE)
    django.setup()

from admin_panel.admin_panel.models import User, Channel, Flow, Post
from bot.services.user_service import UserService
from bot.services.channel_service import ChannelService
from bot.services.flow_service import FlowService
from bot.services.post_service import PostService
from bot.services.post_service import PostRepository
from bot.services.draft_service import DraftService
from bot.services.aisettings_service import AISettingsService
from bot.services.subscription_service import SubscriptionService
from bot.services.payment_service import PaymentService
from bot.services.statistics_service import StatisticsService
from bot.services.userbot_service import UserbotService, EnhancedUserbotService