import asyncio
import subprocess
import time
import logging
from aiogram.types import CallbackQuery
from aiogram_dialog.widgets.kbd import Button, Row
from aiogram_dialog import DialogManager, StartMode

from dialogs.generation.states import GenerationMenu
from bot.dialogs.generation.add_channel.states import AddChannelMenu
from bot.dialogs.generation.create_flow.states import CreateFlowMenu

from bot.dialogs.generation.flow.states import FlowMenu

from bot.containers import Container
from bot.tasks import force_flows_generation_task

logger = logging.getLogger(__name__)


async def go_back_to_channels(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager
):
    channel = manager.dialog_data.get("selected_channel") or manager.start_data.get('selected_channel')
    channel_flow = manager.dialog_data.get("channel_flow") or manager.start_data.get('channel_flow')

    await manager.start(
        GenerationMenu.channel_main,
        data={
            "selected_channel": channel,
            "channel_flow": channel_flow,
            "item_id": str(channel.id)
        },
    )

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
        manager.dialog_data['item_id'] = item_id
        
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
    item_id = manager.dialog_data.get('item_id')

    if not channel_flow:
        await callback.answer(f"У канала {selected_channel.name} поки немає Флоу")
        return
    await manager.start(
        FlowMenu.posts_list,
        data={
            "selected_channel": selected_channel,
            "channel_flow": channel_flow,
            "channel_id": item_id
            },
        mode=StartMode.RESET_STACK 
    )

async def on_create_flow(callback: CallbackQuery, button: Button, manager: DialogManager):
    selected_channel = manager.dialog_data.get("selected_channel")
    channel_flow = manager.dialog_data.get('channel_flow')
    if channel_flow:
        await callback.answer(f"У канала {selected_channel.name} вже є Флоу")
        return
    await manager.start(
        CreateFlowMenu.select_theme,
        data={"selected_channel": selected_channel},
        mode=StartMode.RESET_STACK 
    )

async def on_buffer(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(GenerationMenu.buffer)

async def on_book_recall(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(GenerationMenu.book_recall)


async def on_force_generate(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager
):
    try:
        dialog_data = manager.dialog_data
        flow = dialog_data.get("channel_flow")
        
        if not flow:
            await callback.answer(
                "⚠️ Не обрано флоу для генерації",
                show_alert=True
            )
            return

        await callback.answer()
        
        await callback.message.answer(
            f"⚡ Розпочато генерацію контенту для флоу *{flow.name}*...",
            parse_mode="Markdown"
        )

        subprocess.Popen([
            "python", "generator_worker.py",
            str(flow.id),
            str(callback.message.chat.id),
        ])

    except Exception as e:
        logging.error(f"Помилка запуску генерації: {str(e)}", exc_info=True)
        await callback.answer(
            "⚠️ Сталася помилка під час запуску генерації",
            show_alert=True
        )