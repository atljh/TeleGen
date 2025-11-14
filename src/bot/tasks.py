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
            # Update next generation time even on error to prevent infinite loops
            await flow_service.update_next_generation_time(flow.id)
            continue


async def _publish_scheduled_posts():
    post_service = Container.post_service()
    logger.info("Checking for scheduled posts...")
    await post_service.publish_scheduled_posts()


async def _deactivate_expired_subscriptions():
    now = timezone.now()
    logger.info("Checking for expired and scheduled subscriptions...")

    try:
        expired_subscriptions = await sync_to_async(list)(
            Subscription.objects.filter(
                is_active=True,
                end_date__lt=now
            ).select_related('user', 'tariff_period__tariff')
        )

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

        if deactivated_count > 0:
            logger.info(f"✅ Deactivated {deactivated_count} expired subscriptions")
        else:
            logger.info("No expired subscriptions found")

        scheduled_subscriptions = await sync_to_async(list)(
            Subscription.objects.filter(
                is_active=False,
                start_date__lte=now,
                end_date__gt=now
            ).select_related('user', 'tariff_period__tariff')
            .order_by('user')
        )

        # Group subscriptions by user and select the best one for each user
        users_subscriptions = {}
        for subscription in scheduled_subscriptions:
            user_id = subscription.user_id
            if user_id not in users_subscriptions:
                users_subscriptions[user_id] = []
            users_subscriptions[user_id].append(subscription)

        users_processed = set()
        activated_count = 0

        for user_id, user_subs in users_subscriptions.items():
            if user_id in users_processed:
                continue

            # Select the best subscription: highest tariff level, then longest period, then newest
            best_subscription = max(
                user_subs,
                key=lambda s: (
                    s.tariff_period.tariff.level,  # Higher level is better
                    s.tariff_period.months,         # Longer period is better
                    s.id                             # Newer subscription is better
                )
            )

            subscription = best_subscription
            users_processed.add(user_id)

            # Log the selection if there were multiple options
            if len(user_subs) > 1:
                logger.info(
                    f"User {user_id} has {len(user_subs)} scheduled subscriptions. "
                    f"Selected best: #{subscription.id} "
                    f"({subscription.tariff_period.tariff.name} - {subscription.tariff_period.months}m, "
                    f"level: {subscription.tariff_period.tariff.level})"
                )

            other_active = await sync_to_async(list)(
                Subscription.objects.filter(
                    user=subscription.user,
                    is_active=True
                ).exclude(id=subscription.id)
            )

            for old_sub in other_active:
                old_sub.is_active = False
                await sync_to_async(old_sub.save)(update_fields=['is_active'])
                logger.info(
                    f"Deactivated old subscription {old_sub.id} for user {subscription.user.id} "
                    f"to activate scheduled subscription {subscription.id}"
                )

            subscription.is_active = True
            await sync_to_async(subscription.save)(update_fields=['is_active'])

            logger.info(
                f"Activated scheduled subscription {subscription.id} for user {subscription.user.id} "
                f"(tariff: {subscription.tariff_period.tariff.name}, "
                f"started: {subscription.start_date})"
            )
            activated_count += 1

            # Clean up other scheduled subscriptions that were not activated (downgrades/duplicates)
            if len(user_subs) > 1:
                other_scheduled = [s for s in user_subs if s.id != subscription.id]
                for other_sub in other_scheduled:
                    # Set end_date to now to prevent re-activation
                    other_sub.end_date = now
                    await sync_to_async(other_sub.save)(update_fields=['end_date'])
                    logger.info(
                        f"Expired unactivated scheduled subscription {other_sub.id} for user {user_id} "
                        f"({other_sub.tariff_period.tariff.name} - {other_sub.tariff_period.months}m, "
                        f"level: {other_sub.tariff_period.tariff.level}) - was not better than activated subscription"
                    )

        if activated_count > 0:
            logger.info(f"✅ Activated {activated_count} scheduled subscriptions")
        else:
            logger.info("No scheduled subscriptions to activate")

        from django.db.models import Count
        users_with_multiple_subs = await sync_to_async(list)(
            Subscription.objects.filter(is_active=True)
            .values('user')
            .annotate(sub_count=Count('id'))
            .filter(sub_count__gt=1)
        )

        cleaned_count = 0
        for user_data in users_with_multiple_subs:
            user_id = user_data['user']

            user_subscriptions = await sync_to_async(list)(
                Subscription.objects.filter(
                    user_id=user_id,
                    is_active=True
                ).select_related('user', 'tariff_period__tariff')
                .order_by('-id')
            )

            if len(user_subscriptions) > 1:
                for old_sub in user_subscriptions[1:]:
                    old_sub.is_active = False
                    await sync_to_async(old_sub.save)(update_fields=['is_active'])

                    logger.info(
                        f"Deactivated old subscription {old_sub.id} for user {old_sub.user.id} "
                        f"(user had {len(user_subscriptions)} active subscriptions, "
                        f"kept the newest: {user_subscriptions[0].id})"
                    )
                    cleaned_count += 1

        if cleaned_count > 0:
            logger.info(f"✅ Cleaned up {cleaned_count} duplicate active subscriptions")

    except Exception as e:
        logger.error(f"Error managing subscriptions: {e}", exc_info=True)
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
