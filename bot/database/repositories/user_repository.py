from admin_panel.admin_panel.models import User
from bot.database.exceptions import UserNotFoundError


class UserRepository:
    async def get_or_create_user(self, telegram_id: int, username: str | None = None) -> tuple[User, bool]:
        return await User.objects.aget_or_create(
            telegram_id=telegram_id,
            defaults={"username": username}
        )

    async def get_user_by_telegram_id(self, telegram_id: int) -> User:
        try:
            return await User.objects.aget(telegram_id=telegram_id)
        except User.DoesNotExist:
            raise UserNotFoundError(f"User with telegram_id={telegram_id} not found.")

    async def get_user_by_id(self, user_id: int) -> User:
        try:
            return await User.objects.aget(id=user_id)
        except User.DoesNotExist:
            raise UserNotFoundError(f"User with id={user_id} not found.")

    async def update_user(self, user: User) -> User:
        await user.asave()
        return user

    async def delete_user(self, user: User):
        await user.adelete()
