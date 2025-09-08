from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup

from bot.containers import Container

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    user_service = Container.user_service()
    user_dto, created = await user_service.create_or_get_user(
        telegram_id=message.from_user.id, username=message.from_user.username
    )
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✨ Генерацiя"), KeyboardButton(text="📂 Буфер")],
            [KeyboardButton(text="⚙️ Налаштування"), KeyboardButton(text="❓ Допомога")],
        ],
        resize_keyboard=True,
    )

    await message.answer(
        "📌 *Вітаємо у PROPOST\!* 🎉\n\n" "Оберіть опцію з меню нижче:\n" "👇👇👇",
        reply_markup=keyboard,
        parse_mode="MarkdownV2",
    )
