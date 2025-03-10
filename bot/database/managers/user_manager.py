from admin_panel.admin_panel.models import User
from bot.database.exceptions import UserNotFoundError


class UserManager:
    @staticmethod
    def get_or_create_user(telegram_id, username=None):
        user, created = User.objects.get_or_create(
            telegram_id=telegram_id,
            defaults={"username": username}
        )
        return user, created

    @staticmethod
    def get_user_by_telegram_id(telegram_id):
        try:
            return User.objects.get(telegram_id=telegram_id)
        except User.DoesNotExist:
            raise UserNotFoundError(f"User with telegram_id={telegram_id} not found.")

    @staticmethod
    def update_user_subscription(telegram_id, subscription_status, subscription_end_date=None):
        user = UserManager.get_user_by_telegram_id(telegram_id)
        user.subscription_status = subscription_status
        if subscription_end_date:
            user.subscription_end_date = subscription_end_date
        user.save()
        return user

    @staticmethod
    def delete_user(telegram_id):
        user = UserManager.get_user_by_telegram_id(telegram_id)
        user.delete()
