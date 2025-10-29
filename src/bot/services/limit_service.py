import logging

from dateutil.relativedelta import relativedelta
from django.utils import timezone

from admin_panel.models import Flow, Tariff, User
from bot.database.exceptions import (
    ChannelLimitExceeded,
    GenerationLimitExceeded,
    SourceLimitExceeded,
)


class LimitService:
    def __init__(self, logger: logging.Logger | None = None):
        self.logger = logger or logging.getLogger(__name__)

    async def get_user_tariff(self, user: User) -> Tariff | None:
        active_sub = (
            await user.subscriptions.filter(is_active=True)
            .select_related("tariff_period__tariff")
            .afirst()
        )
        if active_sub:
            return active_sub.tariff_period.tariff
        return None

    async def _reset_generations_if_needed(self, user: User):
        now = timezone.now()
        if not user.generation_reset_at or now >= user.generation_reset_at:
            user.generated_posts_count = 0
            user.generation_reset_at = now + relativedelta(months=1)
            await user.asave(
                update_fields=["generated_posts_count", "generation_reset_at"]
            )

    async def check_channels_limit(self, user: User):
        tariff = await self.get_user_tariff(user)
        if not tariff:
            return

        user_channels_count = (
            await Flow.objects.filter(channel__user_id=user.id).acount() + 1
        )

        if user_channels_count > tariff.channels_available:
            self.logger.warning(
                f"Користувач {user.id} перевищив ліміт каналів: {user_channels_count}/{tariff.channels_available}"
            )
            raise ChannelLimitExceeded(
                f"❌ Ліміт каналів досягнуто ({tariff.channels_available})"
            )

    async def check_sources_limit(
        self,
        user: User,
        flow: Flow | None = None,
        dialog_sources: list[dict] | None = None,
        source_type: str | None = None,
    ):
        tariff = await self.get_user_tariff(user)
        if not tariff:
            return

        if dialog_sources:
            sources_count = len(dialog_sources)
        elif flow:
            sources_count = len(flow.sources) + 1
        else:
            sources_count = 1

        if sources_count > tariff.sources_available:
            self.logger.warning(
                f"Користувач {user.id} перевищив ліміт джерел для флоу: {sources_count}/{tariff.sources_available}"
            )
            raise SourceLimitExceeded(
                f"❌ Ліміт джерел для одного флоу досягнуто ({tariff.sources_available})"
            )

        await self.check_sources_platform_compatibility(
            tariff=tariff, source_type=source_type
        )

    async def check_sources_platform_compatibility(
        self,
        tariff: Tariff,
        source_type: str | None = None,
    ):
        if not source_type:
            return

        source_type = source_type.lower()

        is_telegram_source = source_type in ["telegram", "tg", "channel"]
        is_web_source = source_type in ["web", "website", "rss", "news"]

        if tariff.platforms == Tariff.PLATFORM_TG and is_web_source:
            raise SourceLimitExceeded(
                "❌ Ваш тариф підтримує тільки Telegram джерела.\n"
            )

        elif tariff.platforms == Tariff.PLATFORM_WEB and is_telegram_source:
            raise SourceLimitExceeded("❌ Ваш тариф підтримує тільки веб-джерела.\n")

    async def check_generations_limit(self, user: User, new_generations: int = 0):
        await self._reset_generations_if_needed(user)
        tariff = await self.get_user_tariff(user)
        if not tariff:
            return

        if user.generated_posts_count + new_generations > tariff.generations_available:
            self.logger.warning(
                f"Користувач {user.id} перевищив ліміт генерацій: {user.generated_posts_count + new_generations}/{tariff.generations_available}"
            )
            raise GenerationLimitExceeded(
                f"⚠️ *Ліміт генерацій досягнуто*\n\n"
                f"Згенеровано: {user.generated_posts_count}/{tariff.generations_available} постів\n"
                f"Ліміт оновиться наступного місяця\\.\n\n"
                f"Для збільшення ліміту оновіть тарифний план\\."
            )

    async def increment_generations(self, user: User, count: int = 1):
        await self._reset_generations_if_needed(user)
        user.generated_posts_count += count
        await user.asave(update_fields=["generated_posts_count", "generation_reset_at"])

    async def decrement_generations(self, user: User, count: int = 1):
        await self._reset_generations_if_needed(user)
        user.generated_posts_count = max(0, user.generated_posts_count - count)
        await user.asave(update_fields=["generated_posts_count", "generation_reset_at"])
