import logging
from aiogram.types import CallbackQuery
from aiogram_dialog.widgets.kbd import Button, Row
from aiogram_dialog import DialogManager, StartMode

from .states import FlowMenu

async def on_publish_now(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(FlowMenu.publish_now)

async def on_schedule(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(FlowMenu.schedule)

async def on_edit(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(FlowMenu.edit)

async def on_save_to_buffer(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(FlowMenu.save_to_buffer)