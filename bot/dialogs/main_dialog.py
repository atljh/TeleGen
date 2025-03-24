from aiogram.enums import ParseMode
from aiogram.fsm.state import State, StatesGroup
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.kbd import Button, Row

from .handlers import (
    on_generation_click,
    on_buffer_click,
    on_settings_click,
    on_help_click,
)

class MainMenu(StatesGroup):
    main = State()

main_menu_dialog = Dialog(
    Window(
        Format(
            "*Вітаємо у PROPOST\!* 🎉\n\n"
            "Оберіть опцію з меню нижче:\n"
            "👇👇👇"
        ),
        Row(
            Button(Const("✨ Генерація"), id="generation", on_click=on_generation_click),
            Button(Const("📂 Буфер"), id="buffer", on_click=on_buffer_click),
        ),
        Row(
            Button(Const("⚙️ Налаштування"), id="settings", on_click=on_settings_click),
            Button(Const("❓ Допомога"), id="help", on_click=on_help_click),
        ),
        state=MainMenu.main,
        parse_mode=ParseMode.MARKDOWN_V2,
    )
)