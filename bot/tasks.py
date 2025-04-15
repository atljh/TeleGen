import logging
from admin_panel.admin_panel.models import Flow
from celery import shared_task
from django.utils import timezone
from bot.services import FlowService, PostService
from bot.containers import Container
from bot.services import PostService

logger = logging.getLogger(__name__)



@shared_task
def generate_flow_posts(flow_id: int):
    post_service = Container.post_service()
    return post_service.generate_auto_posts(flow_id)

@shared_task
def check_flows_generation():
    flow_service = Container.flow_service()
    post_service = Container.post_service()
    
    flows_to_generate = flow_service.get_flows_for_generation()
    for flow in flows_to_generate:
        generate_flow_posts.delay(flow.id)