from aiogram import types
from aiogram.dispatcher.dispatcher import Dispatcher
from aiogram.filters import Command
from aiogram_dialog import DialogManager, StartMode

from dialogs.main.states import MainMenu
from bot.containers import Container

async def cmd_start(message: types.Message, dialog_manager: DialogManager):
    user = message.from_user
    telegram_id = user.id
    username = user.username

    user_service = Container.user_service()

    db_user_dto, created = await user_service.create_or_get_user(
        telegram_id=telegram_id,
        username=username
    )

    await dialog_manager.start(state=MainMenu.main, mode=StartMode.RESET_STACK)

def register_handlers(dp: Dispatcher):
    dp.message.register(cmd_start, Command("start"))