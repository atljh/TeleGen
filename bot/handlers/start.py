from aiogram import types
from aiogram.dispatcher.dispatcher import Dispatcher
from aiogram.filters import Command
from aiogram_dialog import DialogManager, StartMode

from dialogs.main_dialog import MainMenu
from database.managers.user_manager import UserManager

user_manager = UserManager()


async def cmd_start(message: types.Message, dialog_manager: DialogManager):
    user = message.from_user
    telegram_id = user.id
    username = user.username

    db_user, created = await user_manager.get_or_create_user(
        telegram_id=telegram_id,
        username=username
    )

    if created:
        await message.answer(f"Новый пользователь создан: {db_user}")
    else:
        await message.answer(f"Добро пожаловать обратно, {db_user}!")

    await dialog_manager.start(state=MainMenu.main, mode=StartMode.RESET_STACK)


def register_handlers(dp: Dispatcher):
    dp.message.register(cmd_start, Command("start"))
