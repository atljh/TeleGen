# handlers/start.py
import logging
from aiogram import Router, types
from aiogram.dispatcher.dispatcher import Dispatcher 
from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram_dialog import DialogManager, StartMode
from bot.containers import Container
from dialogs.main.states import MainMenu

router = Router()


@router.message(F.text == "/start")
async def cmd_start(message: Message, dialog_manager: DialogManager):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✨ Генерацiя"), KeyboardButton(text="📂 Буфер")],
            [KeyboardButton(text="⚙️ Налаштування"), KeyboardButton(text="❓ Допомога")],
        ],
        resize_keyboard=True,
    )
    
    await message.answer(
        "Вітаємо у PROPOST! 🎉\n\nОберіть опцію:",
        reply_markup=keyboard
    )
    await dialog_manager.start(MainMenu.main, mode=StartMode.RESET_STACK)

def register_handlers(dp: Dispatcher):
    dp.include_router(router)