import asyncio
import logging


from celery import shared_task

from bot.containers import Container
from bot.generator_worker import _start_telegram_generations

logger = logging.getLogger()


async def _async_check_flows_generation():
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


@shared_task(bind=True, max_retries=3)
def check_flows_generation(self):
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_async_check_flows_generation())
    except Exception as e:
        logger.error(f"Task check_flows_generation failed: {e}")
        self.retry(exc=e, countdown=60)
    finally:
        loop.close()


@shared_task(bind=True, max_retries=3)
def check_scheduled_posts(self):
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            result = loop.run_until_complete(_async_check_scheduled_posts())
            return result
        finally:
            loop.close()

    except Exception as e:
        logger.error(f"Task check_scheduled_posts failed: {e}", exc_info=True)
        self.retry(exc=e, countdown=60)


async def _async_check_scheduled_posts():
    try:
        post_service = Container.post_service()
        logger.info("Checking for scheduled posts...")

        published = await post_service.publish_scheduled_posts()
        if published:
            logger.info(f"Successfully published {len(published)} posts")
        else:
            logger.info("No posts to publish")

        return [post.dict() for post in published]

    except Exception as e:
        logger.error(f"Error publishing scheduled posts: {e}", exc_info=True)
        raise
