import logging
from aiogram.types import CallbackQuery
from aiogram_dialog.widgets.kbd import Button, Row
from aiogram_dialog import DialogManager, StartMode

from .states import GenerationMenu
from bot.dialogs.generation.add_channel.states import AddChannelMenu
from .flow.states import FlowMenu
from .create_flow.states import CreateFlowMenu

logger = logging.getLogger(__name__)

from bot.containers import Container

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
        
        flow_service = Container.flow_service()
        channel_flow = await flow_service.get_flow_by_channel_id(int(item_id))

        manager.dialog_data.update({
            "selected_channel": selected_channel,
            "channel_flow": channel_flow
        })
        
        await manager.switch_to(GenerationMenu.channel_main)
        
    except Exception as e:
        logger.error(f"Channel selection error: {e}", exc_info=True)
        await callback.answer("Error processing selection")

async def add_channel(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.start(AddChannelMenu.instructions)


async def on_flow(callback: CallbackQuery, button: Button, manager: DialogManager):
    selected_channel = manager.dialog_data.get("selected_channel")
    channel_flow = manager.dialog_data.get('channel_flow')
    await manager.start(
        FlowMenu.posts_list,
        data={
            "selected_channel": selected_channel,
            "channel_flow": channel_flow,
            },
        mode=StartMode.RESET_STACK 
    )

async def on_create_flow(callback: CallbackQuery, button: Button, manager: DialogManager):
    selected_channel = manager.dialog_data.get("selected_channel")
    channel_flow = manager.dialog_data.get('channel_flow')
    if channel_flow:
        await callback.answer(f"У канала {selected_channel.name} уже есть Флоу")
        return
    await manager.start(
        CreateFlowMenu.select_source,
        data={"selected_channel": selected_channel},
        mode=StartMode.RESET_STACK 
    )

async def on_buffer(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(GenerationMenu.buffer)

async def on_book_recall(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(GenerationMenu.book_recall)
