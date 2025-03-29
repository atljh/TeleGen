# handlers/start.py
import logging
from aiogram import Router, types
from aiogram.dispatcher.dispatcher import Dispatcher 
from aiogram.filters import Command
from aiogram_dialog import DialogManager, StartMode
from bot.containers import Container
from dialogs.main.states import MainMenu

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message, dialog_manager: DialogManager):
    user = message.from_user
    user_service = Container.user_service()

    await user_service.create_or_get_user(
        telegram_id=user.id,
        username=user.username
    )

    await dialog_manager.start(state=MainMenu.main, mode=StartMode.RESET_STACK)

def register_handlers(dp: Dispatcher):
    dp.include_router(router)