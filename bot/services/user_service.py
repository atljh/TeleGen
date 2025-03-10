from admin_panel.admin_panel.models import User
from bot.database.repositories.user_repository import UserRepository


class UserService:
    def __init__(self):
        self.user_repository = UserRepository()

    async def create_or_get_user(self, telegram_id: int, username: str | None = None) -> tuple[User, bool]:
        return await self.user_repository.get_or_create_user(telegram_id, username)

    async def get_user(self, telegram_id: int) -> User:
        return await self.user_repository.get_user_by_telegram_id(telegram_id)

    async def update_subscription(self, telegram_id: int, subscription_status: bool, subscription_end_date: str | None = None) -> User:
        user = await self.user_repository.get_user_by_telegram_id(telegram_id)
        user.subscription_status = subscription_status
        user.subscription_end_date = subscription_end_date
        return await self.user_repository.update_user(user)

    async def delete_user(self, telegram_id: int):
        user = await self.user_repository.get_user_by_telegram_id(telegram_id)
        await self.user_repository.delete_user(user)
