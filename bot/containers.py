import logging
import os

from aiogram import Bot
from aiogram.client.session.aiohttp import AiohttpSession
from dependency_injector import containers, providers

from bot.database.repositories import (
    AISettingsRepository,
    ChannelRepository,
    DraftRepository,
    FlowRepository,
    PaymentRepository,
    PostRepository,
    StatisticsRepository,
    SubscriptionRepository,
    UserRepository,
)
from bot.services import (
    AISettingsService,
    ChannelService,
    CloudflareBypass,
    ContentProcessorService,
    EnhancedUserbotService,
    FlowService,
    ImageExtractorService,
    PaymentService,
    PostBuilderService,
    PostService,
    RssService,
    StatisticsService,
    SubscriptionService,
    UserService,
    WebScraperService,
    WebService,
)
from bot.services.web.rss_url_manager import RssUrlManager


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(
        modules=["bot.handlers", "bot.dialogs", "bot.services.post.post_service"]
    )

    session = providers.Singleton(AiohttpSession)
    bot = providers.Singleton(
        Bot, token=os.getenv("TELEGRAM_BOT_TOKEN"), session=session
    )

    user_repository = providers.Factory(UserRepository)
    channel_repository = providers.Factory(ChannelRepository)
    flow_repository = providers.Factory(FlowRepository)
    post_repository = providers.Factory(PostRepository)
    draft_repository = providers.Factory(DraftRepository)
    subscription_repository = providers.Factory(SubscriptionRepository)
    payment_repository = providers.Factory(PaymentRepository)
    ai_settings_repository = providers.Factory(AISettingsRepository)
    statistics_repository = providers.Factory(StatisticsRepository)

    ai_settings_service = providers.Factory(
        AISettingsService,
        repository=ai_settings_repository,
        user_repository=user_repository,
    )

    subscription_service = providers.Factory(
        SubscriptionService,
        channel_repository=channel_repository,
        user_repository=user_repository,
        subscription_repository=subscription_repository,
        logger=providers.Singleton(logging.getLogger, "subscription_service"),
    )

    user_service = providers.Factory(
        UserService,
        user_repository=user_repository,
        channel_repository=channel_repository,
        subscription_service=subscription_service,
    )

    userbot_service = providers.Singleton(
        EnhancedUserbotService,
        aisettings_service=ai_settings_service,
        user_service=user_service,
        api_id=os.getenv("USERBOT_API_ID"),
        api_hash=os.getenv("USERBOT_API_HASH"),
        phone=os.getenv("TELEGRAM_PHONE"),
        openai_key=os.getenv("OPENAI_API_KEY"),
        logger=providers.Singleton(logging.getLogger, "userbot_service"),
    )

    rss_service_factory = providers.Factory(
        RssService,
        rss_app_key=os.getenv("RSS_API_KEY"),
        rss_app_secret=os.getenv("RSS_API_SECRET"),
        post_repository=post_repository,
        logger=providers.Singleton(logging.getLogger, "rss_service"),
    )
    channel_service = providers.Factory(
        ChannelService,
        channel_repository=channel_repository,
        user_repository=user_repository,
        rss_service=rss_service_factory,
    )

    flow_service = providers.Factory(
        FlowService,
        rss_service=rss_service_factory,
        flow_repository=flow_repository,
        channel_repository=channel_repository,
    )

    rss_url_manager = providers.Factory(
        RssUrlManager, rss_service=rss_service_factory, flow_service=flow_service
    )
    cloudflare_bypass = providers.Factory(
        CloudflareBypass,
        logger=providers.Singleton(logging.getLogger, "cloudflare_bypass"),
    )

    web_scraper_service = providers.Factory(
        WebScraperService,
        cf_bypass=cloudflare_bypass,
        logger=providers.Singleton(logging.getLogger, "web_scraper"),
    )

    image_extractor_service = providers.Factory(
        ImageExtractorService,
        logger=providers.Singleton(logging.getLogger, "image_extractor"),
    )

    post_builder_service = providers.Factory(
        PostBuilderService,
        logger=providers.Singleton(logging.getLogger, "post_builder"),
    )

    content_processor_service = providers.Factory(
        ContentProcessorService,
        aisettings_service=ai_settings_service,
        openai_key=os.getenv("OPENAI_API_KEY"),
        logger=providers.Singleton(logging.getLogger, "content_processor"),
    )

    web_service = providers.Factory(
        WebService,
        post_repository=post_repository,
        rss_service_factory=rss_service_factory.provider,
        content_processor=content_processor_service,
        user_service=user_service,
        flow_service=flow_service,
        web_scraper=web_scraper_service,
        aisettings_service=ai_settings_service,
        image_extractor=image_extractor_service,
        post_builder=post_builder_service,
        logger=providers.Singleton(logging.getLogger, "web_service"),
    )

    post_service = providers.Factory(
        PostService,
        post_repository=post_repository,
        flow_repository=flow_repository,
        bot=bot,
        userbot_service=userbot_service,
        web_service=web_service,
    )

    payment_service = providers.Factory(
        PaymentService,
        payment_repository=payment_repository,
        logger=providers.Singleton(logging.getLogger, "payment_service"),
    )

    statistics_service = providers.Factory(
        StatisticsService,
        statistics_repository=statistics_repository,
        logger=providers.Singleton(logging.getLogger, "statistics_service"),
    )

    @staticmethod
    async def shutdown_resources():
        container = Container()
        if container.session.provided:
            await container.session().close()
        if container.userbot_service.provided:
            await container.userbot_service().stop()
