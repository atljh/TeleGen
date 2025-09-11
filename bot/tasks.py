import logging
import asyncio
from celery import shared_task

from bot.containers import Container
from bot.generator_worker import _start_telegram_generations

logger = logging.getLogger(__name__)


async def _process_flows():
    flow_service = Container.flow_service()
    post_service = Container.post_service()

    flows = await flow_service.get_flows_due_for_generation()

    for flow in flows:
        logger.info(f"Processing flow {flow.id} (volume: {flow.flow_volume})")
        try:
            await _start_telegram_generations(
                flow, flow_service, post_service, auto_generate=True
            )
        except Exception as e:
            logger.error(f"Failed to process flow {flow.id}: {e}")
            continue

async def _publish_scheduled_posts():
    post_service = Container.post_service()
    logger.info("Checking for scheduled posts...")

    published = await post_service.publish_scheduled_posts()

    if published:
        logger.info(f"Successfully published {len(published)} posts")
    else:
        logger.info("No posts to publish")

    return [post.dict() for post in published]


@shared_task(bind=True, max_retries=3)
def run_scheduled_jobs(self):
    """
    Unified Celery task:
    - Processes flows for generation
    - Publishes scheduled posts
    """
    try:
        async def runner():
            await _process_flows()
            return await _publish_scheduled_posts()

        result = asyncio.run(runner())
        return result

    except Exception as e:
        logger.error(f"run_scheduled_jobs failed: {e}", exc_info=True)
        self.retry(exc=e, countdown=60)
