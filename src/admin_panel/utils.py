import logging
from datetime import timedelta

from django.utils import timezone

from .models import Subscription, Tariff, User

logger = logging.getLogger(__name__)


async def create_trial_subscription_for_user(user: User) -> Subscription | None:

    has_active = await user.subscriptions.filter(is_active=True).aexists()
    if has_active:
        logger.info(
            f"User {user.id} already has active subscription, skipping trial creation"
        )
        return None

    free_tariff = await Tariff.objects.filter(code=Tariff.FREE).afirst()
    if not free_tariff:
        logger.warning(
            f"Free tariff not found. Cannot create trial subscription for user {user.id}"
        )
        return None

    period = await free_tariff.periods.filter(months=1).afirst()
    if not period:
        logger.error(
            f"No trial period found for free tariff. Cannot create trial subscription for user {user.id}"
        )
        return None

    try:
        subscription = await Subscription.objects.acreate(
            user=user,
            tariff_period=period,
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=free_tariff.trial_duration_days),
            is_trial=True,
            is_active=True,
        )
        logger.info(
            f"✅ Created trial subscription for user {user.id} "
            f"(expires: {subscription.end_date}, duration: {free_tariff.trial_duration_days} days)"
        )
        return subscription
    except Exception as e:
        logger.error(
            f"Failed to create trial subscription for user {user.id}: {e}",
            exc_info=True
        )
        return None
