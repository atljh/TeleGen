import logging
from typing import List, Optional
from asgiref.sync import sync_to_async

from bot.database.dtos import ChannelDTO
from bot.database.repositories import (
    ChannelRepository,
    UserRepository
)
from bot.services.logger_service import get_logger


class ChannelService:
    def __init__(
        self,
        channel_repository: ChannelRepository,
        user_repository: UserRepository
    ):
        self.channel_repository = channel_repository
        self.user_repository = user_repository
        self.logger = get_logger()

    async def get_or_create_channel(
        self,
        user_telegram_id: int,
        channel_id: str,
        name: str,
        description: Optional[str] = None
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
                description=description or ""
            )
            
            if not channel:
                raise RuntimeError("Failed to create or get channel")
            
            if self.logger:
                await self.logger.user_created_channel(user, name, channel_id)
            
            logging.info(f"Channel {channel_id} {'created' if created else 'retrieved'} for user {user_telegram_id}")
            
            return ChannelDTO.from_orm(channel), created
            
        except Exception as e:
            logging.error(f"Error in get_or_create_channel for user {user_telegram_id}: {e}")
            if self.logger:
                await self.logger.error_occurred(
                    error_message=f"Channel creation failed: {e}",
                    user=user if 'user' in locals() else None,
                    context={
                        "user_telegram_id": user_telegram_id,
                        "channel_id": channel_id,
                        "channel_name": name
                    }
                )
            raise

    async def get_user_channels(self, user_telegram_id: int) -> List[ChannelDTO]:
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
            
            if self.logger:
                await self.logger.settings_updated(
                    user=channel.user,
                    setting_type="channel",
                    old_value="",
                    new_value=str(kwargs)
                )
            
            logging.info(f"Channel {channel_id} updated with: {kwargs}")
            
            return ChannelDTO.from_orm(updated_channel)
            
        except Exception as e:
            logging.error(f"Error updating channel {channel_id}: {e}")
            if self.logger:
                await self.logger.error_occurred(
                    error_message=f"Channel update failed: {e}",
                    context={"channel_id": channel_id, "updates": kwargs}
                )
            raise

    async def delete_channel(self, channel_id: str):
        try:
            channel = await self.channel_repository.get_channel_by_id(channel_id)
            if not channel:
                raise ValueError(f"Channel with ID {channel_id} not found")
            
            user = await sync_to_async(lambda: channel.user)()
            
            await self.channel_repository.delete_channel(channel)
            
            if self.logger:
                await self.logger.user_deleted_channel(
                    user=user,
                    channel_name=channel.name,
                    channel_id=channel.id
                )
            
            logging.info(f"Channel {channel_id} deleted successfully")
            
        except Exception as e:
            logging.error(f"Error deleting channel {channel_id}: {e}")
            if self.logger:
                await self.logger.error_occurred(
                    error_message=f"Channel deletion failed: {e}",
                    context={"channel_id": channel_id}
                )
            raise