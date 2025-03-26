from aiogram import Bot
from aiogram.types import CallbackQuery
from aiogram_dialog.widgets.kbd import Button, Row
from aiogram_dialog import DialogManager, StartMode

from dialogs.main.states import MainMenu
from .add_channel.states import AddChannelMenu

async def on_channel_selected(callback: CallbackQuery, widget, manager: DialogManager, item_id: str):
    channel = manager.dialog_data["channels"][int(item_id)]
    await callback.answer(f"Selected: {channel.name}")

async def add_channel(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.start(AddChannelMenu.enter_channel_id)

async def go_back_to_main(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.start(MainMenu.main, mode=StartMode.RESET_STACK)
