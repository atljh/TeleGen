from admin_panel.admin_panel.models import Flow
from database.exceptions import FlowNotFoundError
from database.utils.async_orm import AsyncORM


class FlowManager(AsyncORM):
    def create_flow(self, channel, name, source_type, parameters):
        flow = Flow.objects.create(
            channel=channel,
            name=name,
            source_type=source_type,
            parameters=parameters
        )
        return flow

    def get_flows_by_channel(self, channel):
        return Flow.objects.filter(channel=channel)

    def get_flow_by_id(self, flow_id):
        try:
            return Flow.objects.get(id=flow_id)
        except Flow.DoesNotExist:
            raise FlowNotFoundError(f"Flow with id={flow_id} not found.")

    def delete_flow(self, flow_id):
        flow = FlowManager.get_flow_by_id(flow_id)
        flow.delete()
