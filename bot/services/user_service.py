from bot.database.models import UserDTO, FlowDTO
from bot.database.repositories.user_repository import UserRepository
from bot.database.repositories.channel_repository import ChannelRepository
from bot.services.logger_service import get_logger


class UserService:
    def __init__(
        self, user_repository: UserRepository, channel_repository: ChannelRepository
    ):
        self.user_repository = user_repository
        self.channel_repository = channel_repository
        self.logger = get_logger()

    async def create_or_get_user(
        self, telegram_id: int, username: str | None = None
    ) -> tuple[UserDTO, bool]:
        user, created = await self.user_repository.get_or_create_user(
            telegram_id, username
        )
        if created:
            await self.logger.user_registered(user)
        return UserDTO.from_orm(user), created

    async def get_user(self, telegram_id: int) -> UserDTO:
        user = await self.user_repository.get_user_by_telegram_id(telegram_id)
        return UserDTO.from_orm(user)

    async def update_subscription(
        self,
        telegram_id: int,
        subscription_status: bool,
        subscription_end_date: str | None = None,
    ) -> UserDTO:
        user = await self.user_repository.get_user_by_telegram_id(telegram_id)
        user.subscription_status = subscription_status
        user.subscription_end_date = subscription_end_date
        updated_user = await self.user_repository.update_user(user)
        return UserDTO.from_orm(updated_user)

    async def delete_user(self, telegram_id: int):
        user = await self.user_repository.get_user_by_telegram_id(telegram_id)
        await self.user_repository.delete_user(user)

    async def get_user_by_flow(self, flow: FlowDTO) -> UserDTO:
        channel = await self.channel_repository.get_channel(flow.channel_id)
        user = await self.user_repository.get_user_by_id(channel.user_id)
        return user
