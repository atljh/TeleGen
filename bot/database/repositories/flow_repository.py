from admin_panel.admin_panel.models import Flow
from bot.database.exceptions import FlowNotFoundError

class FlowRepository:
    async def create_flow(
        self,
        channel,
        name: str,
        theme: str,
        source: str,
        content_length: str,
        use_emojis: bool,
        use_premium_emojis: bool,
        cta: bool,
        frequency: str
    ) -> Flow:
        return await Flow.objects.acreate(
            channel=channel,
            name=name,
            theme=theme,
            source=source,
            content_length=content_length,
            use_emojis=use_emojis,
            use_premium_emojis=use_premium_emojis,
            cta=cta,
            frequency=frequency
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