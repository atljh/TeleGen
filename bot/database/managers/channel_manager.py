from admin_panel.admin_panel.models import Channel
from database.exceptions import ChannelNotFoundError
from database.utils.async_orm import AsyncORM


class ChannelManager(AsyncORM):
    def create_channel(self, user, channel_name, channel_id):
        channel = Channel.objects.create(
            user=user,
            channel_name=channel_name,
            channel_id=channel_id
        )
        return channel

    def get_channels_by_user(self, user):
        return Channel.objects.filter(user=user)

    def get_channel_by_id(self, channel_id):
        try:
            return Channel.objects.get(self, id=channel_id)
        except Channel.DoesNotExist:
            raise ChannelNotFoundError(f"Channel with id={channel_id} not found.")

    def delete_channel(self, channel_id):
        channel = ChannelManager.get_channel_by_id(channel_id)
        channel.delete()
