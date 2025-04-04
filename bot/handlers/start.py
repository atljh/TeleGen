from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✨ Генерацiя"), KeyboardButton(text="📂 Буфер")],
            [KeyboardButton(text="⚙️ Налаштування"), KeyboardButton(text="❓ Допомога")],
        ],
        resize_keyboard=True,
    )
    
    await message.answer(
        "📌 *Вітаємо у PROPOST\!* 🎉\n\n"
        "Оберіть опцію з меню нижче:\n"
        "👇👇👇",
        reply_markup=keyboard,
        parse_mode="MarkdownV2"
    )