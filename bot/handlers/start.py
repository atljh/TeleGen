from aiogram import types
from aiogram.dispatcher.dispatcher import Dispatcher
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram_dialog import DialogManager, StartMode

from dialogs.main_dialog import MainMenu
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
    # if created:
    #     await message.answer(f"Новый пользователь создан: {db_user_dto.username}")
    # else:
    #     await message.answer(f"Добро пожаловать обратно, {db_user_dto.username}!")

    builder = ReplyKeyboardBuilder()
    builder.row(
        types.KeyboardButton(text="Генерація"),
        types.KeyboardButton(text="Буфер"),
    )
    builder.row(
        types.KeyboardButton(text="Налаштування"),
        types.KeyboardButton(text="Допомога"),
    )

    await message.answer(
        "Вітаємо у PROPOST! Виберіть опцію:",
        reply_markup=builder.as_markup(resize_keyboard=True)
    )

    await dialog_manager.start(state=MainMenu.main, mode=StartMode.RESET_STACK)

def register_handlers(dp: Dispatcher):
    dp.message.register(cmd_start, Command("start"))