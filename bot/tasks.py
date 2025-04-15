import logging
from celery.schedules import crontab
from admin_panel.admin_panel.models import Flow
from bot.celery_app import app
from django.utils import timezone
from bot.services import FlowService, PostService
from bot.containers import Container
from bot.services import PostService

logger = logging.getLogger(__name__)





@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(
        crontab(minute='*/10'),
        check_flows_generation.s(),
        name='check-flows-generation'
    )

@app.task
def check_flows_generation():
    flow_service = Container.flow_service()
    post_service = Container.post_service()
    
    flows = flow_service.get_flows_due_for_generation()
    for flow in flows:
        post_service.generate_auto_posts(flow.id)
        flow_service.update_next_generation_time(flow)