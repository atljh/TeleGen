import logging
from aiogram.types import CallbackQuery
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog import DialogManager, StartMode, Dialog, Window

from bot.containers import Container
from dialogs.main.states import MainMenu

from .states import SettingsMenu

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
        
        await manager.switch_to(SettingsMenu.channel_settings)
        
    except Exception as e:
        logger.error(f"Channel selection error: {e}")
        await callback.answer("Error processing selection")

async def pay_subscription(callback: CallbackQuery, button: Button, manager: DialogManager):
    await callback.message.answer("Оплата пiдписки")

async def go_back_to_main(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.start(MainMenu.main, mode=StartMode.RESET_STACK)

async def confirm_delete_channel(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(SettingsMenu.confirm_delete)

async def delete_channel(callback: CallbackQuery, button: Button, manager: DialogManager):
    channel_service = Container.channel_service() 
    channel = manager.dialog_data['selected_channel']
    await channel_service.delete_channel(channel.channel_id)
    await callback.answer(f"Канал {channel.name} видалено")
    await manager.switch_to(SettingsMenu.main)

async def cancel_delete_channel(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(SettingsMenu.channel_main_settings)