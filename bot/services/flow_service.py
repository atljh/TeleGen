import logging
from datetime import datetime, timedelta
from django.utils import timezone
from bot.database.dtos import FlowDTO
from bot.database.dtos import ContentLength, GenerationFrequency
from bot.database.repositories import FlowRepository, ChannelRepository
from bot.database.exceptions import ChannelNotFoundError, FlowNotFoundError

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
        channel = await self.channel_repository.get_channel_by_id(channel_id)
        
        if isinstance(content_length, ContentLength):
            content_length = content_length.value
            
        if isinstance(frequency, GenerationFrequency):
            frequency = frequency.value
        try:
            flow = await self.flow_repository.create_flow(
                channel=channel,
                name=name,
                theme=theme,
                sources=sources,
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
        except Exception as e:
            logger.error(f"Flow error {e}", exc_info=True)
            return
        try:
            flow_dto = FlowDTO.from_orm(flow)
        except Exception as e:
            logger.error(f"DTO conversion error: {e}", exc_info=True)
            return
        return FlowDTO.from_orm(flow)

    async def get_flow_by_channel_id(self, channel_id: int) -> FlowDTO | None:
        try:
            return await self.flow_repository.get_flow_by_channel_id(channel_id)
        except FlowNotFoundError:
            return None

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
            if not flow:
                raise ValueError(f"Flow with ID {flow_id} not found")
            
            for field, value in kwargs.items():
                setattr(flow, field, value)
            
            updated_flow = await self.flow_repository.update_flow(flow)
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

    async def get_flows_due_for_generation(self) -> list[FlowDTO]:
        now = timezone.now()
        flows = await self.flow_repo.list(
            is_auto_generated=True,
            next_generation_time__lte=now
        )
        return flows
    
    async def update_next_generation_time(self, flow: FlowDTO):
        """Обновляет время следующей генерации"""
        if flow.frequency == "hourly":
            next_time = timezone.now() + timedelta(hours=1)
        elif flow.frequency == "12h":
            next_time = timezone.now() + timedelta(hours=12)
        elif flow.frequency == "daily":
            next_time = timezone.now() + timedelta(days=1)
        else:
            next_time = None
        
        await self.flow_repo.update(
            flow.id,
            next_generation_time=next_time,
            last_generated_at=timezone.now()
        )