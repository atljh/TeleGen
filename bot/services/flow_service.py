import logging
from datetime import datetime
from bot.database.dtos import FlowDTO
from bot.database.dtos import ContentLength, GenerationFrequency
from bot.database.repositories import FlowRepository, ChannelRepository
from bot.database.exceptions import ChannelNotFoundError

logger = logging.getLogger(__name__)

class FlowService:
    def __init__(self, flow_repository: FlowRepository, channel_repository: ChannelRepository):
        self.flow_repository = flow_repository
        self.channel_repository = channel_repository

    async def create_flow(
        self,
        channel_id: int,
        name: str,
        theme: str,
        sources: list[dict],
        content_length: ContentLength | str,
        use_emojis: bool,
        use_premium_emojis: bool,
        title_highlight: bool,
        cta: bool,
        frequency: GenerationFrequency | str,
        signature: str | None = None,
        flow_volume: int = 5,          
        ad_time: str | None = None
    ) -> FlowDTO:
        try:
            channel = await self.channel_repository.get_channel_by_id(channel_id)

            if isinstance(content_length, ContentLength):
                content_length = content_length.value
                
            if isinstance(frequency, GenerationFrequency):
                frequency = frequency.value

            flow = await self.flow_repository.create_flow(
                channel=channel,
                name=name,
                theme=theme,
                sources=[{"url": url} for url in sources],
                content_length=content_length,
                use_emojis=use_emojis,
                use_premium_emojis=use_premium_emojis,
                title_highlight=title_highlight,
                cta=cta,
                frequency=frequency,
                signature=signature,
                flow_volume=flow_volume,
                ad_time=ad_time,
            )
            
            return FlowDTO.from_orm(flow)
            
        except ChannelNotFoundError as e:
            logger.error(f"Channel {channel_id} not found")
            raise
        except Exception as e:
            logger.error(f"Error creating flow: {e}")
            raise

    async def get_flow_by_id(self, flow_id: int) -> FlowDTO:
        try:
            flow = await self.flow_repository.get_flow_by_id(flow_id)
            return FlowDTO.from_orm(flow)
        except Exception as e:
            logger.error(f"Error getting flow {flow_id}: {e}")
            raise

    async def get_user_flows(self, user_id: int) -> list[FlowDTO]:
        try:
            flows = await self.flow_repository.get_user_flows(user_id)
            return [FlowDTO.from_orm(f) for f in flows]
        except Exception as e:
            logger.error(f"Error getting flows for user {user_id}: {e}")
            raise

    async def update_flow(self, flow_id: int, **kwargs) -> FlowDTO:
        try:
            flow = await self.flow_repository.get_flow_by_id(flow_id)
            updated_flow = await self.flow_repository.update_flow(flow, **kwargs)
            return FlowDTO.from_orm(updated_flow)
        except Exception as e:
            logger.error(f"Error updating flow {flow_id}: {e}")
            raise

    async def delete_flow(self, flow_id: int):
        try:
            flow = await self.flow_repository.get_flow_by_id(flow_id)
            await self.flow_repository.delete_flow(flow)
            logger.info(f"Deleted flow {flow_id}")
        except Exception as e:
            logger.error(f"Error deleting flow {flow_id}: {e}")
            raise