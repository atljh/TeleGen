import logging

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

    async def check_sources_limit(self, user: User, new_flow: Flow | None = None):
        tariff = await self.get_user_tariff(user)
        if not tariff:
            return

        flows_sources = await Flow.objects.filter(channel__user_id=user.id).values_list(
            "sources", flat=True
        )
        sources_total = sum(len(sources) for sources in flows_sources)
        if new_flow:
            sources_total += len(new_flow.sources)

        if sources_total > tariff.sources_available:
            self.logger.warning(
                f"Користувач {user.id} перевищив ліміт джерел: {sources_total}/{tariff.sources_available}"
            )
            raise SourceLimitExceeded(
                f"❌ Ліміт джерел досягнуто ({tariff.sources_available})"
            )

    async def check_generations_limit(self, user: User, new_generations: int = 0):
        tariff = await self.get_user_tariff(user)
        if not tariff:
            return

        if (
            user.generated_posts_count + new_generations
        ) > tariff.generations_available:
            self.logger.warning(
                f"Користувач {user.id} перевищив ліміт генерацій: {user.generated_posts_count + new_generations}/{tariff.generations_available}"
            )
            raise GenerationLimitExceeded(
                f"❌ Ліміт генерацій досягнуто ({tariff.generations_available}/місяць)"
            )

    async def increment_generations(self, user: User, count: int = 1):
        user.generated_posts_count += count
        await user.save(update_fields=["generated_posts_count"])

    async def decrement_generations(self, user: User, count: int = 1):
        user.generated_posts_count = max(0, user.generated_posts_count - count)
        await user.save(update_fields=["generated_posts_count"])
