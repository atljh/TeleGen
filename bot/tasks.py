import asyncio
import logging
from typing import List

from celery import shared_task

from bot.containers import Container
from bot.generator_worker import _start_telegram_generations

logger = logging.getLogger()


async def remove_old_posts(flow_id: int, count: int, post_service):
    old_posts = await post_service.get_oldest_posts(flow_id, count)
    logger.info(f"Removing {len(old_posts)} old posts for flow {flow_id}")

    for post in old_posts:
        await post_service.delete_post(post.id)


async def create_new_posts(flow_id: int, posts_dto: List, post_service):
    created_posts = []
    for post_data in posts_dto:
        media_list = [
            {"path": img.url, "type": "image", "order": img.order}
            for img in post_data.images
        ]
        if post_data.video_url:
            media_list.append(
                {
                    "path": post_data.video_url,
                    "type": "video",
                    "order": len(post_data.images),
                }
            )

        post = await post_service.create_post(
            original_link=post_data.original_link,
            original_date=post_data.original_date,
            flow_id=flow_id,
            content=post_data.content,
            media_list=media_list,
        )
        created_posts.append(post)

    if created_posts:
        logger.info(f"Created {len(created_posts)} new posts for flow {flow_id}")


async def _async_check_flows_generation():
    flow_service = Container.flow_service()
    post_service = Container.post_service()

    flows = await flow_service.get_flows_due_for_generation()
    logger.info(f"Found {len(flows)} flows due for generation")

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
