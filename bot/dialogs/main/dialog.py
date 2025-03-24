from aiogram.enums import ParseMode
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.kbd import Button, Row

from .states import MainMenu
from .callbacks import (
    on_generation_click,
    on_buffer_click,
    # on_settings_click,
    # on_help_click,
)

def create_main_dialog():
    return Dialog(
        Window(
            Format(
                "*Вітаємо у PROPOST\\!* 🎉\n\n"
                "Оберіть опцію з меню нижче\\:\n"
                "👇👇👇"
            ),
            Row(
                Button(Const("✨ Генерация"), id="generation", on_click=on_generation_click),
                Button(Const("📂 Буфер"), id="buffer", on_click=on_buffer_click),
            ),
            # ... остальные кнопки
            state=MainMenu.main,
            parse_mode=ParseMode.MARKDOWN_V2,
        )
    )