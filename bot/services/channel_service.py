import logging
from asgiref.sync import sync_to_async

from admin_panel.admin_panel.models import Flow
from bot.database.models.channel import ChannelDTO
from bot.database.repositories import ChannelRepository, UserRepository
from bot.services.logger_service import get_logger
from bot.services.web.rss_service import RssService


class ChannelService:
    def __init__(
        self,
        channel_repository: ChannelRepository,
        user_repository: UserRepository,
        rss_service: RssService,
    ):
        self.channel_repository = channel_repository
        self.user_repository = user_repository
        self.rss_service = rss_service
        self.logger = get_logger()

    async def get_or_create_channel(
        self,
        user_telegram_id: int,
        channel_id: str,
        name: str,
        description: str | None = None,
    ) -> tuple[ChannelDTO, bool]:
        """
        Get or create channel for user

        Args:
            user_telegram_id: User's Telegram ID
            channel_id: Channel ID (from Telegram)
            name: Channel name
            description: Optional channel description

        Returns:
            Tuple of (ChannelDTO, created_flag)

        Raises:
            ValueError: Invalid input parameters
            RuntimeError: Failed to create/get channel
        """
        try:
            if not isinstance(user_telegram_id, int) or user_telegram_id <= 0:
                raise ValueError("Invalid user Telegram ID")

            if not channel_id or not isinstance(channel_id, str):
                raise ValueError("Invalid channel ID")

            if not name or not isinstance(name, str):
                raise ValueError("Invalid channel name")

            user = await self.user_repository.get_user_by_telegram_id(user_telegram_id)
            if not user:
                raise ValueError(f"User with Telegram ID {user_telegram_id} not found")

            channel, created = await self.channel_repository.get_or_create_channel(
                user=user,
                channel_id=channel_id,
                name=name,
                description=description or "",
            )

            if not channel:
                raise RuntimeError("Failed to create or get channel")

            if self.logger:
                await self.logger.user_created_channel(user, name, channel_id)

            return ChannelDTO.from_orm(channel), created

        except Exception as e:
            logging.error(
                f"Error in get_or_create_channel for user {user_telegram_id}: {e}"
            )
            if self.logger:
                await self.logger.error_occurred(
                    error_message=f"Channel creation failed: {e}",
                    user=user if "user" in locals() else None,
                    context={
                        "user_telegram_id": user_telegram_id,
                        "channel_id": channel_id,
                        "channel_name": name,
                    },
                )
            raise

    async def get_user_channels(self, user_telegram_id: int) -> list[ChannelDTO]:
        try:
            user = await self.user_repository.get_user_by_telegram_id(user_telegram_id)
            if not user:
                raise ValueError(f"User with Telegram ID {user_telegram_id} not found")

            channels = await self.channel_repository.get_user_channels(user)

            return [ChannelDTO.from_orm(channel) for channel in channels]

        except Exception as e:
            logging.error(f"Error getting channels for user {user_telegram_id}: {e}")
            raise

    async def get_channel_by_db_id(self, channel_id: int) -> ChannelDTO:
        try:
            channel = await self.channel_repository.get_channel(channel_id)
            if not channel:
                raise ValueError(f"Channel with ID {channel_id} not found")

            return ChannelDTO.from_orm(channel)

        except Exception as e:
            logging.error(f"Error getting channel by ID {channel_id}: {e}")
            raise

    async def get_channel_by_telegram_id(self, channel_id: str) -> ChannelDTO:
        try:
            channel = await self.channel_repository.get_channel_by_id(channel_id)
            if not channel:
                raise ValueError(f"Channel with Telegram ID {channel_id} not found")

            return ChannelDTO.from_orm(channel)

        except Exception as e:
            logging.error(f"Error getting channel by Telegram ID {channel_id}: {e}")
            raise

    async def update_channel(self, channel_id: int, **kwargs) -> ChannelDTO:
        try:
            channel = await self.channel_repository.get_channel(channel_id)
            if not channel:
                raise ValueError(f"Channel with ID {channel_id} not found")

            # valid_fields = {'name', 'description', 'is_active'}
            # for field in kwargs.keys():
            #     if field not in valid_fields:
            #         raise ValueError(f"Invalid field for update: {field}")

            for field, value in kwargs.items():
                setattr(channel, field, value)

            updated_channel = await self.channel_repository.update_channel(channel)
            user = await sync_to_async(lambda: channel.user)()

            if self.logger:
                await self.logger.settings_updated(
                    user=user,
                    setting_type="channel",
                    old_value="",
                    new_value=str(kwargs),
                )

            logging.info(f"Channel {channel_id} updated with: {kwargs}")

            return ChannelDTO.from_orm(updated_channel)

        except Exception as e:
            logging.error(f"Error updating channel {channel_id}: {e}")
            if self.logger:
                await self.logger.error_occurred(
                    error_message=f"Channel update failed: {e}",
                    context={"channel_id": channel_id, "updates": kwargs},
                )
            raise

    async def delete_channel(self, channel_id: str):
        """
        Delete channel and all associated RSS feeds

        Args:
            channel_id: Telegram channel ID to delete

        Raises:
            ValueError: Channel not found
            Exception: Error during deletion
        """
        try:
            channel = await self.channel_repository.get_channel_by_id(channel_id)
            if not channel:
                raise ValueError(f"Channel with ID {channel_id} not found")

            user = await sync_to_async(lambda: channel.user)()
            channel_name = channel.name

            await self._delete_associated_rss_feeds(channel_id)

            await self.channel_repository.delete_channel(channel)

            if self.logger:
                await self.logger.user_deleted_channel(
                    user=user, channel_name=channel_name, channel_id=channel_id
                )

            logging.info(
                f"Channel {channel_id} successfully deleted with all associated RSS feeds"
            )

        except Exception as e:
            logging.error(f"Error deleting channel {channel_id}: {e}")
            if self.logger:
                await self.logger.error_occurred(
                    error_message=f"Channel deletion failed: {e}",
                    context={"channel_id": channel_id},
                )
            raise

    async def _delete_associated_rss_feeds(self, channel_id: str):
        """
        Delete all RSS feeds associated with the channel

        Args:
            channel_id: Telegram channel ID

        Note:
            Continues deletion even if some feeds fail to delete
        """
        try:
            flows = await sync_to_async(list)(
                Flow.objects.filter(channel__channel_id=channel_id)
            )

            if not flows:
                logging.info(f"No flows found for channel {channel_id}")
                return

            deleted_count = 0
            failed_count = 0

            for flow in flows:
                if not flow.sources:
                    continue

                for source in flow.sources:
                    if source.get("type") == "web" and source.get("rss_url"):
                        try:
                            success = await self.rss_service.delete_feed_by_url(
                                source["rss_url"]
                            )
                            if success:
                                deleted_count += 1
                                logging.info(
                                    f"Successfully deleted RSS feed: {source['rss_url']}"
                                )
                            else:
                                failed_count += 1
                                logging.warning(
                                    f"Failed to delete RSS feed: {source['rss_url']}"
                                )
                        except Exception as e:
                            failed_count += 1
                            logging.error(
                                f"Error deleting RSS feed {source['rss_url']}: {e}"
                            )

            logging.info(
                f"RSS feeds cleanup for channel {channel_id}: "
                f"{deleted_count} deleted, {failed_count} failed"
            )

        except Exception as e:
            logging.error(f"Error in RSS feeds cleanup for channel {channel_id}: {e}")
