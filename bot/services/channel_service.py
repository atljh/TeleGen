from bot.database.dtos import ChannelDTO
from bot.database.repositories.channel_repository import ChannelRepository


class ChannelService:
    def __init__(self, channel_repository: ChannelRepository):
        self.channel_repository = channel_repository

    async def get_or_create_channel(
        self,
        user,
        channel_id: str,
        name: str,
        description: str | None = None
    ) -> tuple[ChannelDTO, bool]:
        channel, created = await self.channel_repository.get_or_create_channel(
            user, channel_id, name, description
        )
        return ChannelDTO.from_orm(channel), created
    
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