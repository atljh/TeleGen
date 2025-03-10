from bot.database.managers.user_manager import UserManager
from bot.database.exceptions import UserNotFoundError


class UserService:
    def __init__(self):
        self.user_manager = UserManager()

    async def create_or_get_user(self, telegram_id, username=None):
        return await self.user_manager.get_or_create_user(
            telegram_id=telegram_id,
            username=username
        )

    async def get_user(self, telegram_id):
        try:
            return await self.user_manager.get_user_by_telegram_id(telegram_id)
        except UserNotFoundError:
            return None

    async def update_subscription(self, telegram_id, subscription_status, subscription_end_date=None):
        return await self.user_manager.update_user_subscription(
            telegram_id=telegram_id,
            subscription_status=subscription_status,
            subscription_end_date=subscription_end_date
        )

    async def delete_user(self, telegram_id):
        await self.user_manager.delete_user(telegram_id)
