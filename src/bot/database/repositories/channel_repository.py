import logging

from admin_panel.models import Channel, User
from admin_panel.utils import create_trial_subscription_for_user
from bot.database.exceptions import ChannelNotFoundError

logger = logging.getLogger(__name__)


class ChannelRepository:
    async def get_or_create_channel(
        self, user: User, channel_id: str, name: str, description: str | None = None
    ) -> tuple[Channel, bool]:
        channel, created = await Channel.objects.aget_or_create(
            user=user,
            channel_id=channel_id,
            defaults={"name": name, "description": description, "is_active": True},
        )

        # Если это первый канал пользователя - выдаем trial подписку
        if created:
            user_channels_count = await Channel.objects.filter(user=user).acount()
            if user_channels_count == 1:
                logger.info(
                    f"Creating first channel for user {user.id}, granting trial subscription"
                )
                await create_trial_subscription_for_user(user)

        return channel, created

    async def get_user_channels(self, user: User) -> list[Channel]:
        return [
            channel
            async for channel in Channel.objects.filter(user=user).order_by(
                "-created_at"
            )
        ]

    async def get_channel(self, id: int) -> Channel:
        try:
            return await Channel.objects.aget(id=id)
        except Channel.DoesNotExist as e:
            raise ChannelNotFoundError(f"Channel with id={id} not found.") from e

    async def get_channel_by_id(self, channel_id: str) -> Channel:
        try:
            return await Channel.objects.aget(channel_id=channel_id)
        except Channel.DoesNotExist as e:
            raise ChannelNotFoundError(
                f"Channel with channel_id={channel_id} not found."
            ) from e

    async def update_channel(self, channel: Channel) -> Channel:
        await channel.asave()
        return channel

    async def delete_channel(self, channel: Channel):
        await channel.adelete()
