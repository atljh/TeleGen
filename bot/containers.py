from dependency_injector import containers, providers
from aiogram import Bot
from aiogram.client.session.aiohttp import AiohttpSession
from bot.database.repositories import (
    UserRepository,
    ChannelRepository,
    FlowRepository,
    PostRepository,
    DraftRepository,
    SubscriptionRepository,
    PaymentRepository,
    AISettingsRepository,
    StatisticsRepository,
)
from bot.services import (
    UserService,
    ChannelService,
    FlowService,
    PostService,
    DraftService,
    SubscriptionService,
    PaymentService,
    AISettingsService,
    StatisticsService,
    UserbotService
)
import os

class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(
        modules=[
            "handlers",
            "dialogs",
            "bot.services.post_service"
        ]
    )
    
    session = providers.Singleton(AiohttpSession)
    bot = providers.Singleton(
        Bot,
        token=os.getenv("TELEGRAM_BOT_TOKEN"),
        session=session
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

    user_service = providers.Factory(
        UserService,
        user_repository=user_repository,
    )
    userbot_service = providers.Singleton(
        UserbotService,
        api_id=os.getenv("USERBOT_API_ID"),
        api_hash=os.getenv("USERBOT_API_HASH"),
        phone=os.getenv("TELEGRAM_PHONE")
    )
    channel_service = providers.Factory(
        ChannelService,
        channel_repository=channel_repository,
        user_repository=user_repository
    )

    flow_service = providers.Factory(
        FlowService,
        flow_repository=flow_repository,
        channel_repository=channel_repository
    )

    post_service = providers.Factory(
        PostService,
        post_repository=post_repository,
        flow_repository=flow_repository,
        bot=bot,
        userbot_service=userbot_service
    )

    draft_service = providers.Factory(
        DraftService,
        draft_repository=draft_repository,
    )

    subscription_service = providers.Factory(
        SubscriptionService,
        subscription_repository=subscription_repository,
    )

    payment_service = providers.Factory(
        PaymentService,
        payment_repository=payment_repository,
    )

    ai_settings_service = providers.Factory(
        AISettingsService,
        ai_settings_repository=ai_settings_repository,
    )

    statistics_service = providers.Factory(
        StatisticsService,
        statistics_repository=statistics_repository,
    )