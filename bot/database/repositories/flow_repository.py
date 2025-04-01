from datetime import datetime
from admin_panel.admin_panel.models import Flow
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
        return await Flow.objects.acreate(
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
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

    async def get_flow_by_id(self, flow_id: int) -> Flow:
        try:
            return await Flow.objects.aget(id=flow_id)
        except Flow.DoesNotExist:
            raise FlowNotFoundError(f"Flow with id={flow_id} not found.")

    async def update_flow(self, flow: Flow) -> Flow:
        await flow.asave()
        return flow

    async def delete_flow(self, flow: Flow):
        await flow.adelete()