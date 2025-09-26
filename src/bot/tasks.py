import asyncio
import logging

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
                flow,
                flow_service,
                post_service,
                allow_partial=True,
                auto_generate=True,
            )
        except Exception as e:
            logger.error(f"Failed to process flow {flow.id}: {e}")
            continue


async def _publish_scheduled_posts():
    post_service = Container.post_service()
    logger.info("Checking for scheduled posts...")
    await post_service.publish_scheduled_posts()


def _get_or_create_event_loop():
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            raise RuntimeError("Loop is closed")
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop


@shared_task(bind=True, max_retries=3)
def run_scheduled_jobs(self):
    try:
        loop = _get_or_create_event_loop()

        if loop.is_running():

            async def runner():
                await _process_flows()
                return await _publish_scheduled_posts()

            task = asyncio.ensure_future(runner(), loop=loop)
            return loop.run_until_complete(task)
        else:
            return loop.run_until_complete(_run_all_tasks())

    except Exception as e:
        logger.error(f"run_scheduled_jobs failed: {e}", exc_info=True)
        self.retry(exc=e, countdown=60)


async def _run_all_tasks():
    await _process_flows()
    return await _publish_scheduled_posts()
