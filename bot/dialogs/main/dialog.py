from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.text import Format
from aiogram_dialog import DialogManager
from aiogram.enums.parse_mode import ParseMode
from aiogram_dialog.api.entities import StartMode

from .states import MainMenu



def create_main_dialog():
    return Dialog(
        Window(
            Format("*Головне меню*"),
            state=MainMenu.main,
            parse_mode=ParseMode.MARKDOWN_V2,
        )
    )