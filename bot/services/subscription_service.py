import logging
from datetime import datetime

from dateutil.relativedelta import relativedelta

from admin_panel.admin_panel.models import Tariff, TariffPeriod
from bot.database.exceptions import (
    ChannelNotFoundError,
    SubscriptionNotFoundError,
    TariffPeriodNotFoundError,
    UserNotFoundError,
)
from bot.database.models import SubscriptionDTO
from bot.database.repositories import (
    ChannelRepository,
    SubscriptionRepository,
    UserRepository,
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
        self, user_id: int, tariff_code: str, months: int | None = None
    ) -> SubscriptionDTO:
        try:
            tariff_codes = {
                "free": Tariff.FREE,
                "basic": Tariff.BASIC,
                "pro": Tariff.PRO,
            }

            if tariff_code not in tariff_codes:
                raise ValueError(f"Неизвестный тариф: {tariff_code}")

            user = await self.user_repository.get_user_by_id(user_id)

            tariff = await Tariff.objects.aget(code=tariff_codes[tariff_code])

            if months:
                tariff_period = await TariffPeriod.objects.aget(
                    tariff=tariff, months=months
                )
            else:
                tariff_period = (
                    await TariffPeriod.objects.filter(tariff=tariff)
                    .order_by("months")
                    .afirst()
                )

            if not tariff_period:
                raise TariffPeriodNotFoundError(
                    f"Не найден период для тарифа {tariff.code}"
                )

            start_date = datetime.now()
            end_date = start_date + relativedelta(months=tariff_period.months)

            subscription = await self.subscription_repository.create_subscription(
                user=user,
                tariff_period=tariff_period,
                start_date=start_date,
                end_date=end_date,
                is_active=True,
            )
            return SubscriptionDTO.from_orm(subscription)

        except Tariff.DoesNotExist as e:
            raise TariffPeriodNotFoundError(f"Тариф {tariff_code} не найден.") from e
        except TariffPeriod.DoesNotExist as e:
            raise TariffPeriodNotFoundError(
                f"Тарифный период для {tariff_code} не найден."
            ) from e
        except UserNotFoundError as e:
            raise UserNotFoundError(f"Пользователь с id={user_id} не найден.") from e

    async def get_subscription_by_id(self, subscription_id: int) -> SubscriptionDTO:
        try:
            subscription = await self.subscription_repository.get_subscription_by_id(
                subscription_id
            )
            return SubscriptionDTO.from_orm(subscription)
        except SubscriptionNotFoundError as e:
            raise SubscriptionNotFoundError(
                f"Подписка с id={subscription_id} не найдена."
            ) from e

    async def update_subscription(
        self,
        subscription_id: int,
        subscription_type: str | None = None,
        start_date=None,
        end_date=None,
        is_active: bool | None = None,
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

        except SubscriptionNotFoundError as e:
            raise SubscriptionNotFoundError(
                f"Подписка с id={subscription_id} не найдена."
            ) from e

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
        except SubscriptionNotFoundError as e:
            raise SubscriptionNotFoundError(
                f"Подписка с id={subscription_id} не найдена."
            ) from e

    async def delete_subscription(self, subscription_id: int):
        try:
            subscription = await self.subscription_repository.get_subscription_by_id(
                subscription_id
            )
            await self.subscription_repository.delete_subscription(subscription)
        except SubscriptionNotFoundError as e:
            raise SubscriptionNotFoundError(
                f"Подписка с id={subscription_id} не найдена."
            ) from e

    async def get_user_subscriptions(self, user_id: int) -> list[SubscriptionDTO]:
        try:
            user = await self.user_repository.get_user_by_id(user_id)
            subscriptions = (
                await self.subscription_repository.get_subscriptions_by_user(user)
            )
            return [SubscriptionDTO.from_orm(sub) for sub in subscriptions]
        except UserNotFoundError as e:
            raise UserNotFoundError(f"Пользователь с id={user_id} не найден.") from e

    async def get_channel_subscriptions(self, channel_id: int) -> list[SubscriptionDTO]:
        try:
            channel = await self.channel_repository.get_channel_by_id(channel_id)
            subscriptions = (
                await self.subscription_repository.get_subscriptions_by_channel(channel)
            )
            return [SubscriptionDTO.from_orm(sub) for sub in subscriptions]
        except ChannelNotFoundError as e:
            raise ChannelNotFoundError(f"Канал с id={channel_id} не найден.") from e
