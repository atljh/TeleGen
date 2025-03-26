from bot.database.dtos import ChannelDTO
from bot.database.repositories import (
    ChannelRepository,
    UserRepository
)
from bot.database.dtos import UserDTO

class ChannelService:
    def __init__(
        self,
        channel_repository: ChannelRepository,
        user_repository: UserRepository
    ):
        self.channel_repository = channel_repository
        self.user_repository = user_repository

    async def get_or_create_channel(
        self,
        user_telegram_id: int,
        channel_id: str,
        name: str,
        description: str | None = None
    ) -> tuple[ChannelDTO, bool]:
        user = await self.user_repository.get_user_by_telegram_id(user_telegram_id)
        
        if not user:
            raise ValueError(f"User with id {user.id} not found")
        
        channel, created = await self.channel_repository.get_or_create_channel(
            user=user,
            channel_id=channel_id,
            name=name,
            description=description
        )
        return ChannelDTO.from_orm(channel), created
    
    async def get_user_channels(self, user_id: int) -> list[ChannelDTO]:
        channels = await self.channel_repository.get_user_channels(user_id)
        return [ChannelDTO.from_orm(channel) for channel in channels]
    
    async def get_channel(self, channel_id: str) -> ChannelDTO:
        channel = await self.channel_repository.get_channel_by_id(channel_id)
        return ChannelDTO.from_orm(channel)
    
    async def update_channel(self, channel_id: str) -> ChannelDTO:
        channel = await self.channel_repository.get_channel_by_id(channel_id)
        updated_channel = await self.channel_repository.update_channel(channel)
        return ChannelDTO.from_orm(updated_channel)
        

    async def delete_user(self, channel_id: str):
        channel =  await self.channel_repository.get_channel_by_id(channel_id)
        await self.channel_repository.delete_channel(channel)