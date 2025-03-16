from typing import List
from admin_panel.admin_panel.models import Flow
from database.exceptions import FlowNotFoundError


class FlowManager:
    async def get_flow_by_id(self, flow_id: int) -> Flow:
        try:
            return await Flow.objects.aget(id=flow_id)
        except Flow.DoesNotExist:
            raise FlowNotFoundError(f"Flow with id={flow_id} not found.")

    async def create_flow(self, channel, name, source_type, parameters) -> Flow:
        return await Flow.objects.acreate(
            channel=channel,
            name=name,
            source_type=source_type,
            parameters=parameters
        )

    async def get_flows_by_channel(self, channel) -> List[Flow]:
        return Flow.objects.filter(channel=channel)
    
    async def update_flow(self, flow: Flow) -> Flow:
        await flow.asave()
        return flow

    async def delete_flow(self, flow: Flow):
        await flow.delete()
