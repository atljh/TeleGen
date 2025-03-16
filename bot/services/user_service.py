from bot.database.dtos import UserDTO
from bot.database.repositories.user_repository import UserRepository

class UserService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def create_or_get_user(self, telegram_id: int, username: str | None = None) -> tuple[UserDTO, bool]:
        user, created = await self.user_repository.get_or_create_user(telegram_id, username)
        return UserDTO.from_orm(user), created

    async def get_user(self, telegram_id: int) -> UserDTO:
        user = await self.user_repository.get_user_by_telegram_id(telegram_id)
        return UserDTO.from_orm(user)

    async def update_subscription(self, telegram_id: int, subscription_status: bool, subscription_end_date: str | None = None) -> UserDTO:
        user = await self.user_repository.get_user_by_telegram_id(telegram_id)
        user.subscription_status = subscription_status
        user.subscription_end_date = subscription_end_date
        updated_user = await self.user_repository.update_user(user)
        return UserDTO.from_orm(updated_user)

    async def delete_user(self, telegram_id: int):
        user = await self.user_repository.get_user_by_telegram_id(telegram_id)
        await self.user_repository.delete_user(user)