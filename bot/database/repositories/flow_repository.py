import logging
from datetime import datetime
from admin_panel.admin_panel.models import Flow
from bot.database.dtos import GenerationFrequency
from bot.database.exceptions import FlowNotFoundError

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
            logging.info(f"Flow created successfully {flow.id}")
            return flow
        except Exception as e:
            logging.error(f"Error during flow creation: {e}", exc_info=True)

    async def get_flow_by_channel_id(self, channel_id: int) -> Flow:
        try:
            return await Flow.objects.aget(channel_id=channel_id)
        except Flow.DoesNotExist:
            raise FlowNotFoundError(f"No flow found for channel {channel_id}")

    async def get_flows_by_channel_id(self, channel_id: int) -> list[Flow]:
        return await Flow.objects.filter(channel_id=channel_id).first()

    async def update_flow(self, flow: Flow) -> Flow:
        await flow.asave()
        return flow

    async def delete_flow(self, flow: Flow):
        await flow.adelete()