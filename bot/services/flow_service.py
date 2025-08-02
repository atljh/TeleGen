import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
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
        try:
            flow = await self.flow_repository.get_flow_by_id(flow_id)
            if not flow:
                raise FlowNotFoundError(f"Flow with ID {flow_id} not found")

            source_to_update = None
            for source in flow.sources:
                if source.get("link") == link:
                    if "rss_url" in source and source["rss_url"]:
                        return source["rss_url"]
                    source_to_update = source
                    break

            if not source_to_update:
                raise ValueError(f"Source with link {link} not found in flow {flow_id}")

            rss_url = await self._discover_rss_for_source(source_to_update)
            if not rss_url:
                logger.warning(f"No RSS feed found for link {link}")
                return None

            updated_sources = []
            for source in flow.sources:
                if source.get("link") == link:
                    source["rss_url"] = rss_url
                updated_sources.append(source)

            await self.update_flow(flow_id, sources=updated_sources)
            logger.info(f"Set and returned rss_url for source {link} in flow {flow_id}")
            return rss_url

        except Exception as e:
            logger.error(f"Error in get_or_set_source_rss_url for flow {flow_id}: {e}", exc_info=True)
            return None


    async def _discover_rss_for_source(self, source: dict) -> str | None:
        
        base_url = source['link'].rstrip('/')

        '''
        Disabled because of multuplty website inner rss bugs
        '''
        # for path in self.common_rss_paths:
        #     rss_url = f"{base_url}{path}"
        #     if await self._validate_rss_feed(rss_url):
        #         return rss_url
        
        if self.rss_app_key and self.rss_app_secret:
            try:
                return await self._get_rss_via_api(base_url)
            except Exception as e:
                self.logger.warning(f"RSS.app API failed for {base_url}: {str(e)}")
        else:
            self.logger.error(f"RSS_APP_KEY or RSS_APP_SECRET not found")

        return None