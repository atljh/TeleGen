from admin_panel.admin_panel.models import Subscription
from bot.database.exceptions import SubscriptionNotFoundError


class SubscriptionRepository:
    async def create_subscription(
        self,
        user,
        channel,
        subscription_type: str,
        start_date,
        end_date,
        is_active: bool = True,
    ) -> Subscription:
        return await Subscription.objects.acreate(
            user=user,
            channel=channel,
            subscription_type=subscription_type,
            start_date=start_date,
            end_date=end_date,
            is_active=is_active,
        )

    async def get_subscription_by_id(self, subscription_id: int) -> Subscription:
        try:
            return await Subscription.objects.aget(id=subscription_id)
        except Subscription.DoesNotExist:
            raise SubscriptionNotFoundError(
                f"Subscription with id={subscription_id} not found."
            )

    async def update_subscription(self, subscription: Subscription) -> Subscription:
        await subscription.asave()
        return subscription

    async def delete_subscription(self, subscription: Subscription):
        await subscription.adelete()
