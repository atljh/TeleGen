from aiogram.enums.parse_mode import ParseMode
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.api.entities import StartMode
from aiogram_dialog.widgets.text import Format


async def on_main_dialog_start(start_data, dialog_manager: DialogManager):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✨ Генерацiя"), KeyboardButton(text="📂 Буфер")],
            [KeyboardButton(text="⚙️ Налаштування"), KeyboardButton(text="❓ Допомога")],
        ],
        resize_keyboard=True,
    )

    event = dialog_manager.event
    if hasattr(event, "message"):
        message = event.message
    else:
        message = event

    await message.answer("Оберіть опцію з меню нижче:", reply_markup=keyboard)


def create_main_dialog():
    return Dialog(
        Window(
            Format(
                "*Вітаємо у PROPOST\\!* 🎉\n\n" "Оберіть опцію з меню нижче\\:\n" "👇👇👇"
            ),
            parse_mode=ParseMode.HTML,
        ),
        on_start=on_main_dialog_start,
    )
