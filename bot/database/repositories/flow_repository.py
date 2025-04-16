import logging
from datetime import datetime
from admin_panel.admin_panel.models import Flow
from bot.database.dtos import GenerationFrequency
from bot.database.exceptions import FlowNotFoundError
from typing import List, Optional
from django.db import models
from datetime import datetime
from django.db.models import Q
from bot.database.dtos.dtos import FlowDTO
from functools import reduce
import operator

class FlowRepository:
    async def create_flow(
        self,
        channel,
        name: str,
        theme: str,
        sources: list[dict],
        content_length: str,
        use_emojis: bool,
        use_premium_emojis: bool,
        title_highlight: bool,
        cta: bool,
        frequency: str,
        signature: str | None = None,
        flow_volume: int = 5,
        ad_time: str | None = None,
    ) -> Flow:
        valid_frequencies = [f.value for f in GenerationFrequency]
        if frequency not in valid_frequencies:
            raise ValueError(f"Invalid frequency. Allowed: {valid_frequencies}")
        try:
            flow = await Flow.objects.acreate(
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
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            return flow
        except Exception as e:
            logging.error(f"Error during flow creation: {e}", exc_info=True)

    async def exists(self, flow_id: int) -> bool:
        return await Flow.objects.filter(id=flow_id).aexists()

    async def get_flow_by_id(self, id: int) -> Flow:
        try:
            return await Flow.objects.aget(id=id)
        except Flow.DoesNotExist:
            raise FlowNotFoundError(f"No flow found with id {id}")

    async def get_flow_by_channel_id(self, channel_id: int) -> Flow:
        try:
            return await Flow.objects.aget(channel_id=channel_id)
        except Flow.DoesNotExist:
            raise FlowNotFoundError(f"No flow found for channel {channel_id}")

    async def get_flows_by_channel_id(self, channel_id: int) -> list[Flow]:
        return await Flow.objects.filter(channel_id=channel_id).first()

    async def update_flow(self, flow: Flow) -> Flow:
        try:
            await flow.asave()
            return flow
        except Exception as e:
            logging.error(f"Error saving flow {flow.id}: {e}")
            raise

    async def delete_flow(self, flow: Flow):
        await flow.adelete()
    
    async def list(
        self,
        next_generation_time__lte: datetime | None = None,
        include_null_generation_time: bool = False,
        limit: int = 100,
        offset: int = 0
    ) -> list[FlowDTO]:
        queryset = Flow.objects.select_related('channel')
        
        conditions = []
        if next_generation_time__lte is not None:
            conditions.append(models.Q(next_generation_time__lte=next_generation_time__lte))
        if include_null_generation_time:
            conditions.append(models.Q(next_generation_time__isnull=True))
        
        if conditions:
            queryset = queryset.filter(reduce(operator.or_, conditions))

        queryset = queryset.order_by('-created_at')
        if limit is not None:
            queryset = queryset[offset:offset+limit]

        return [self._to_dto(flow) async for flow in queryset]

    def _to_dto(self, flow: Flow) -> FlowDTO:
        return FlowDTO(
            id=flow.id,
            channel_id=flow.channel.id,
            name=flow.name,
            theme=flow.theme,
            sources=flow.sources,
            content_length=flow.content_length,
            use_emojis=flow.use_emojis,
            use_premium_emojis=flow.use_premium_emojis,
            title_highlight=flow.title_highlight,
            cta=flow.cta,
            frequency=flow.frequency,
            signature=flow.signature,
            flow_volume=flow.flow_volume,
            ad_time=flow.ad_time,
            next_generation_time=flow.next_generation_time,
            created_at=flow.created_at,
            updated_at=flow.updated_at
        )