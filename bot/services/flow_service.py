import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from django.utils import timezone
from asgiref.sync import sync_to_async

from bot.database.models.flow import ContentLength, FlowDTO, GenerationFrequency
from bot.database.models.user import UserDTO
from bot.database.repositories import FlowRepository, ChannelRepository
from bot.database.exceptions import ChannelNotFoundError, FlowNotFoundError
from bot.services.web.rss_service import RssService

logger = logging.getLogger(__name__)

class FlowService:
    def __init__(
        self,
        flow_repository: FlowRepository,
        channel_repository: ChannelRepository,
        rss_service: RssService
    ):
        self.flow_repository = flow_repository
        self.channel_repository = channel_repository
        self.rss_service = rss_service

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

    async def get_flows_due_for_generation(self) -> List[FlowDTO]:
        now = timezone.now()
        flows = await self.flow_repository.list(
            next_generation_time__lte=now,
            include_null_generation_time=True,
            limit=None
        )
        return flows

    async def force_flows_due_for_generation(self) -> List[FlowDTO]:
        flows = await self.flow_repository.list()
        return flows
    
    async def update_next_generation_time(self, flow_id: int):
        flow = await self.flow_repository.get_flow_by_id(flow_id)
        if flow.frequency == "hourly":
            next_time = timezone.now() + timedelta(hours=1)
        elif flow.frequency == "12h":
            next_time = timezone.now() + timedelta(hours=12)
        elif flow.frequency == "daily":
            next_time = timezone.now() + timedelta(days=1)
        else:
            next_time = None
        
        await self.update_flow(
            flow.id,
            next_generation_time=next_time,
            last_generated_at=timezone.now()
        )

    async def get_or_set_source_rss_url(self, flow_id: int, link: str) -> str | None:
        flow = await self.flow_repository.get_flow_by_id(flow_id)
        if not flow:
            raise FlowNotFoundError(f"Flow with ID {flow_id} not found")

        source = next((s for s in flow.sources if s.get("link") == link), None)
        if not source:
            raise ValueError(f"Source with link {link} not found in flow {flow_id}")
        
        if source.get("type") != "web":
            return None

        if source.get("rss_url"):
            return source["rss_url"]

        rss_url = await self.rss_service._discover_rss_for_source(source)
        if not rss_url:
            logger.warning(f"No RSS feed found for web link {link}")
            return None

        updated_sources = [
            {**s, "rss_url": rss_url} if s.get("link") == link and s.get("type") == "web" else s
            for s in flow.sources
        ]
        await self.update_flow(flow_id, sources=updated_sources)
        return rss_url
    
    async def get_user_by_flow_id(self, flow_id: int) -> UserDTO:
        flow = self.get_flow_by_id(flow_id)
        user = await sync_to_async(lambda: flow.channel)()
        logging.info(user)
        user1 = await sync_to_async(lambda: flow.channel.user)()
        logging.info(user1)

