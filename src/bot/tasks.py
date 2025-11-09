import asyncio
import logging
import os

from asgiref.sync import sync_to_async
from celery import shared_task
from django.utils import timezone

from admin_panel.models import Subscription
from bot.containers import Container
from bot.generator_worker import _start_telegram_generations

logger = logging.getLogger(__name__)


async def _process_flows():
    flow_service = Container.flow_service()
    post_service = Container.post_service()
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")

    flows = await flow_service.get_flows_due_for_generation()

    for flow in flows:
        logger.info(f"Processing flow {flow.id} (volume: {flow.flow_volume})")
        try:
            # Get user for the flow to send notifications
            user = await flow_service.get_user_by_flow_id(flow.id)
            chat_id = user.telegram_id if user else None

            await _start_telegram_generations(
                flow,
                flow_service,
                post_service,
                chat_id,
                bot_token,
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


async def _deactivate_expired_subscriptions():
    """
    Деактивирует истекшие подписки.
    Проверяет все активные подписки и деактивирует те, у которых истек срок.
    """
    now = timezone.now()
    logger.info("Checking for expired subscriptions...")

    try:
        # Получаем все активные подписки с истекшим сроком
        expired_subscriptions = await sync_to_async(list)(
            Subscription.objects.filter(
                is_active=True,
                end_date__lt=now
            ).select_related('user', 'tariff_period__tariff')
        )

        if not expired_subscriptions:
            logger.info("No expired subscriptions found")
            return

        deactivated_count = 0
        for subscription in expired_subscriptions:
            subscription.is_active = False
            await sync_to_async(subscription.save)(update_fields=['is_active'])

            logger.info(
                f"Deactivated expired subscription {subscription.id} for user {subscription.user.id} "
                f"(tariff: {subscription.tariff_period.tariff.name}, "
                f"trial: {subscription.is_trial}, "
                f"expired: {subscription.end_date})"
            )
            deactivated_count += 1

        logger.info(f"✅ Deactivated {deactivated_count} expired subscriptions")

    except Exception as e:
        logger.error(f"Error deactivating expired subscriptions: {e}", exc_info=True)
        raise


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
    await _publish_scheduled_posts()
    return await _deactivate_expired_subscriptions()


@shared_task(bind=True, max_retries=3)
def deactivate_expired_subscriptions_task(self):
    try:
        loop = _get_or_create_event_loop()

        if loop.is_running():
            task = asyncio.ensure_future(_deactivate_expired_subscriptions(), loop=loop)
            return loop.run_until_complete(task)
        else:
            return loop.run_until_complete(_deactivate_expired_subscriptions())

    except Exception as e:
        logger.error(f"deactivate_expired_subscriptions_task failed: {e}", exc_info=True)
        self.retry(exc=e, countdown=300)
