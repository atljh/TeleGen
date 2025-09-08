import logging
from typing import List
from bot.database.models import SubscriptionDTO
from bot.database.repositories import (
    SubscriptionRepository,
    ChannelRepository,
    UserRepository,
)
from bot.database.exceptions import (
    SubscriptionNotFoundError,
    ChannelNotFoundError,
    UserNotFoundError,
)


class SubscriptionService:
    def __init__(
        self,
        subscription_repository: SubscriptionRepository,
        channel_repository: ChannelRepository,
        user_repository: UserRepository,
        logger: logging.Logger | None = None,
    ):
        self.subscription_repository = subscription_repository
        self.channel_repository = channel_repository
        self.user_repository = user_repository
        self.logger = logger or logging.getLogger(__name__)

    async def create_subscription(
        self,
        user_id: int,
        channel_id: int,
        subscription_type: str,
        start_date,
        end_date,
        is_active: bool = True,
    ) -> SubscriptionDTO:
        try:
            user = await self.user_repository.get_user_by_id(user_id)
            channel = await self.channel_repository.get_channel_by_id(channel_id)

            subscription = await self.subscription_repository.create_subscription(
                user=user,
                channel=channel,
                subscription_type=subscription_type,
                start_date=start_date,
                end_date=end_date,
                is_active=is_active,
            )
            return SubscriptionDTO.from_orm(subscription)

        except UserNotFoundError:
            raise UserNotFoundError(f"Пользователь с id={user_id} не найден.")
        except ChannelNotFoundError:
            raise ChannelNotFoundError(f"Канал с id={channel_id} не найден.")

    async def get_subscription_by_id(self, subscription_id: int) -> SubscriptionDTO:
        try:
            subscription = await self.subscription_repository.get_subscription_by_id(
                subscription_id
            )
            return SubscriptionDTO.from_orm(subscription)
        except SubscriptionNotFoundError:
            raise SubscriptionNotFoundError(
                f"Подписка с id={subscription_id} не найдена."
            )

    async def update_subscription(
        self,
        subscription_id: int,
        subscription_type: str = None,
        start_date=None,
        end_date=None,
        is_active: bool = None,
    ) -> SubscriptionDTO:
        try:
            subscription = await self.subscription_repository.get_subscription_by_id(
                subscription_id
            )

            if subscription_type:
                subscription.subscription_type = subscription_type
            if start_date:
                subscription.start_date = start_date
            if end_date:
                subscription.end_date = end_date
            if is_active is not None:
                subscription.is_active = is_active

            updated_subscription = (
                await self.subscription_repository.update_subscription(subscription)
            )
            return SubscriptionDTO.from_orm(updated_subscription)

        except SubscriptionNotFoundError:
            raise SubscriptionNotFoundError(
                f"Подписка с id={subscription_id} не найдена."
            )

    async def deactivate_subscription(self, subscription_id: int) -> SubscriptionDTO:
        try:
            subscription = await self.subscription_repository.get_subscription_by_id(
                subscription_id
            )
            subscription.is_active = False
            updated_subscription = (
                await self.subscription_repository.update_subscription(subscription)
            )
            return SubscriptionDTO.from_orm(updated_subscription)
        except SubscriptionNotFoundError:
            raise SubscriptionNotFoundError(
                f"Подписка с id={subscription_id} не найдена."
            )

    async def delete_subscription(self, subscription_id: int):
        try:
            subscription = await self.subscription_repository.get_subscription_by_id(
                subscription_id
            )
            await self.subscription_repository.delete_subscription(subscription)
        except SubscriptionNotFoundError:
            raise SubscriptionNotFoundError(
                f"Подписка с id={subscription_id} не найдена."
            )

    async def get_user_subscriptions(self, user_id: int) -> List[SubscriptionDTO]:
        try:
            user = await self.user_repository.get_user_by_id(user_id)
            subscriptions = (
                await self.subscription_repository.get_subscriptions_by_user(user)
            )
            return [SubscriptionDTO.from_orm(sub) for sub in subscriptions]
        except UserNotFoundError:
            raise UserNotFoundError(f"Пользователь с id={user_id} не найден.")

    async def get_channel_subscriptions(self, channel_id: int) -> List[SubscriptionDTO]:
        try:
            channel = await self.channel_repository.get_channel_by_id(channel_id)
            subscriptions = (
                await self.subscription_repository.get_subscriptions_by_channel(channel)
            )
            return [SubscriptionDTO.from_orm(sub) for sub in subscriptions]
        except ChannelNotFoundError:
            raise ChannelNotFoundError(f"Канал с id={channel_id} не найден.")
