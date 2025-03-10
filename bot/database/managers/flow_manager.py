from admin_panel.admin_panel.models import Flow
from database.exceptions import FlowNotFoundError


class FlowManager:
    @staticmethod
    def create_flow(channel, name, source_type, parameters):
        flow = Flow.objects.create(
            channel=channel,
            name=name,
            source_type=source_type,
            parameters=parameters
        )
        return flow

    @staticmethod
    def get_flows_by_channel(channel):
        return Flow.objects.filter(channel=channel)

    @staticmethod
    def get_flow_by_id(flow_id):
        try:
            return Flow.objects.get(id=flow_id)
        except Flow.DoesNotExist:
            raise FlowNotFoundError(f"Flow with id={flow_id} not found.")

    @staticmethod
    def delete_flow(flow_id):
        flow = FlowManager.get_flow_by_id(flow_id)
        flow.delete()
