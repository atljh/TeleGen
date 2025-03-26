from admin_panel.admin_panel.models import Channel, User
from bot.database.exceptions import ChannelNotFoundError


class ChannelRepository:
    async def get_or_create_channel(
        self,
        user: User,
        channel_id: str,
        name: str,
        description: str | None = None
    ) -> tuple[Channel, bool]:
        return await Channel.objects.aget_or_create(
            user=user,
            channel_id=channel_id,
            defaults={
                "name": name,
                "description": description,
                "is_active": True
            }
        )

    async def get_channel_by_id(self, channel_id: str) -> Channel:
        try:
            return await Channel.objects.aget(channel_id=channel_id)
        except Channel.DoesNotExist:
            raise ChannelNotFoundError(f"Channel with channel_id={channel_id} not found.")

    async def update_channel(self, channel: Channel) -> Channel:
        await channel.asave()
        return channel

    async def delete_channel(self, channel: Channel):
        await channel.adelete()