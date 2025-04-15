import logging
from admin_panel.admin_panel.models import Flow
from celery import shared_task
from django.utils import timezone
from bot.services import FlowService, PostService


logger = logging.getLogger(__name__)

@shared_task
def generate_auto_posts():
    flow_service = FlowService()
    post_service = PostService()
    
    now = timezone.now()
    flows = Flow.objects.filter(
        is_auto_generated=True,
        next_generation_time__lte=now
    )
    
    for flow in flows:
        try:
            generated_content = generate_content_with_userbot(flow)
            
            # Создание поста
            post_service.create(
                flow=flow,
                content=generated_content,
                status="draft" if flow.needs_review else "approved"
            )
            
            # Обновление времени следующей генерации
            flow_service.update_next_generation_time(flow)
            
        except Exception as e:
            logger.error(f"Ошибка генерации поста для флоу {flow.id}: {str(e)}")