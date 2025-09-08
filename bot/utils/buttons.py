import logging
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager, StartMode
from aiogram_dialog.widgets.kbd import Button

from bot.dialogs.generation.states import GenerationMenu


async def go_back_to_generation(
    callback: CallbackQuery, button: Button, manager: DialogManager
):
    await manager.start(GenerationMenu.main, mode=StartMode.RESET_STACK)


async def go_back_to_channel(
    callback: CallbackQuery, button: Button, manager: DialogManager
):
    selected_channel = manager.dialog_data.get("selected_channel")
    channel_flow = manager.dialog_data.get("channel_flow")
    await manager.start(
        GenerationMenu.channel_main,
        data={
            "selected_channel": selected_channel,
            "channel_flow": channel_flow,
        },
        mode=StartMode.RESET_STACK,
    )
