import logging

from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager, StartMode
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.input import MessageInput

from bot.dialogs.generation.add_channel.states import AddChannelMenu 
from bot.dialogs.generation.create_flow.states import CreateFlowMenu

from bot.dialogs.generation.states import GenerationMenu
from bot.containers import Container


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

async def subscribe(callback: CallbackQuery, button: Button, manager: DialogManager):
    await callback.answer("Функція в розробці")