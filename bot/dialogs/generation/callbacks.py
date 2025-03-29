import logging
from aiogram.types import CallbackQuery
from aiogram_dialog.widgets.kbd import Button, Row
from aiogram_dialog import DialogManager, StartMode

from dialogs.main.states import MainMenu
from .states import GenerationMenu
from .add_channel.states import AddChannelMenu
from .flow.states import FlowMenu
from .create_flow.states import CreateFlowMenu

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
        selected_channel = next(
            (channel for channel in channels if str(channel.id) == item_id),
            None
        )
        
        if not selected_channel:
            await callback.answer("Channel not found!")
            return
            
        manager.dialog_data["selected_channel"] = selected_channel
        
        await manager.switch_to(GenerationMenu.channel_main)
        
    except Exception as e:
        logger.error(f"Channel selection error: {e}")
        await callback.answer("Error processing selection")

async def add_channel(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.start(AddChannelMenu.instructions)

async def go_back_to_main(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.start(MainMenu.main, mode=StartMode.RESET_STACK)


async def on_flow(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.start(FlowMenu.main)

async def on_create_flow(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.start(CreateFlowMenu.select_source)

async def on_buffer(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(GenerationMenu.buffer)

async def on_book_recall(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(GenerationMenu.book_recall)

