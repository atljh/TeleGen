from bot.database.dtos import FlowDTO
from bot.database.repositories import FlowRepository, ChannelRepository
from bot.database.exceptions import ChannelNotFoundError


class FlowService:
    def __init__(self, flow_repository: FlowRepository, channel_repository: ChannelRepository):
        self.flow_repository = flow_repository
        self.channel_repository = channel_repository

    async def create_flow(
        self,
        channel_id: int,
        name: str,
        theme: str,
        source: str,
        content_length: str,
        use_emojis: bool,
        cta: bool,
        frequency: str
        ) -> FlowDTO:
        channel = await self.channel_repository.get_channel_by_id(channel_id)
        try:
            channel = await self.channel_repository.get_channel_by_id(channel_id)
        except ChannelNotFoundError as e:
            raise ChannelNotFoundError(f"Channel with id={channel_id} not found.") from e

        flow = await self.flow_repository.create_flow(
            channel=channel,
            name=name,
            theme=theme,
            source=source,
            content_length=content_length,
            use_emojis=use_emojis,
            cta=cta,
            frequency=frequency
        )
        return FlowDTO.from_orm(flow)
    
    async def get_flow_by_id(self, flow_id: int) -> FlowDTO:
        flow = await self.flow_repository.get_flow_by_id(flow_id)
        return FlowDTO.from_orm(flow)
    
    async def update_flow(self, flow_id) -> FlowDTO:
        flow = await self.flow_repository.get_flow_by_id(flow_id)
        updated_flow = await self.flow_repository.update_flow(flow)
        return FlowDTO.from_orm(updated_flow)

    async def delete_flow(self, flow_id: int):
        flow = await self.flow_repository.get_flow_by_id(flow_id)
        await self.flow_repository.delete_flow(flow)