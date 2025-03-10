from admin_panel.admin_panel.models import Channel
from database.exceptions import ChannelNotFoundError


class ChannelManager:
    @staticmethod
    def create_channel(user, channel_name, channel_id):
        channel = Channel.objects.create(
            user=user,
            channel_name=channel_name,
            channel_id=channel_id
        )
        return channel

    @staticmethod
    def get_channels_by_user(user):
        return Channel.objects.filter(user=user)

    @staticmethod
    def get_channel_by_id(channel_id):
        try:
            return Channel.objects.get(id=channel_id)
        except Channel.DoesNotExist:
            raise ChannelNotFoundError(f"Channel with id={channel_id} not found.")

    @staticmethod
    def delete_channel(channel_id):
        channel = ChannelManager.get_channel_by_id(channel_id)
        channel.delete()