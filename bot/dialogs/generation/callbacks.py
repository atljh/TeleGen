import logging
from aiogram.types import CallbackQuery
from aiogram_dialog.widgets.kbd import Button, Row
from aiogram_dialog import DialogManager, StartMode

from dialogs.main.states import MainMenu
from .states import ChannelMenu
from .add_channel.states import AddChannelMenu

logger = logging.getLogger(__name__)

async def on_channel_selected(
    callback: CallbackQuery,
    widget,
    manager: DialogManager,
    item_id: str
):
    try:
        data = manager.dialog_data
        channels = data.get("channels", [])
        logger.info(f'Channels {channels}')
        selected_channel = next(
            (channel for channel in channels if str(channel.id) == item_id),
            None
        )
        
        if not selected_channel:
            await callback.answer("Channel not found!")
            return
            
        manager.dialog_data["selected_channel"] = selected_channel
        
        await callback.answer(f"Channel {selected_channel.name}")
        await manager.switch_to(ChannelMenu.main)
        
    except Exception as e:
        logger.error(f"Channel selection error: {e}")
        await callback.answer("Error processing selection")

async def add_channel(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.start(AddChannelMenu.enter_channel_id)

async def go_back_to_main(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.start(MainMenu.main, mode=StartMode.RESET_STACK)
