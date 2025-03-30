import logging
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog import DialogManager
from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager, StartMode

from bot.containers import Container
from dialogs.main.states import MainMenu 
from .states import SettingsMenu

logger = logging.getLogger(__name__)


async def open_flow_settings(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(SettingsMenu.flow_settings)