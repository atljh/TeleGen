import logging
from aiogram.types import CallbackQuery
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog import DialogManager, StartMode, Dialog, Window

from bot.containers import Container

from .states import SettingsMenu

logger = logging.getLogger(__name__)


async def on_channel_selected(
    callback: CallbackQuery,
    widget,
    manager: DialogManager,
    item_id: str
):
    try:
        start_data = manager.start_data or {}
        dialog_data = manager.dialog_data or {}
        
        selected_channel = (
            start_data.get("selected_channel") 
            or dialog_data.get("selected_channel")
        )
        channels = (
            start_data.get("channels", [])
            or dialog_data.get("channels", [])
        )
        
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
        
        
        await manager.switch_to(SettingsMenu.channel_settings)
        
    except Exception as e:
        logger.error(f"Channel selection error: {e}")
        await callback.answer("Error processing selection")

async def pay_subscription(callback: CallbackQuery, button: Button, manager: DialogManager):
    await callback.message.answer("Оплата пiдписки")

async def confirm_delete_channel(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(SettingsMenu.confirm_delete)

# ================== ОБРАБОТЧИКИ ОСНОВНЫХ НАСТРОЕК КАНАЛА ==================

async def open_notification_settings(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(SettingsMenu.notification_settings)

async def open_timezone_settings(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(SettingsMenu.timezone_settings)

async def open_emoji_settings(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(SettingsMenu.emoji_settings)

async def open_channel_signature(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(SettingsMenu.channel_signature)

# ================== GETTER ДЛЯ ОКНА НАСТРОЕК ==================

async def selected_channel_getter(dialog_manager: DialogManager, **kwargs):
    channel_service = Container.channel_service()
    selected_channel_id = dialog_manager.dialog_data["selected_channel"].id
    
    try:
        channel = await channel_service.get_channel_by_id(selected_channel_id)
        
        return {
            "selected_channel": channel,
            "channel_flow": dialog_manager.dialog_data.get("channel_flow", None)
        }
    except Exception as e:
        logger.error(f"Error getting channel data: {e}")
        return {
            "selected_channel": None,
            "channel_flow": None
        }

# ================== ОБРАБОТЧИКИ ПОДТВЕРЖДЕНИЯ УДАЛЕНИЯ ==================

async def delete_channel(callback: CallbackQuery, button: Button, manager: DialogManager):
    channel_service = Container.channel_service()
    selected_channel = manager.dialog_data["selected_channel"]
    
    try:
        await channel_service.delete_channel(selected_channel.id)
        await callback.answer("✅ Канал успішно видалено!")
        await manager.done()
    except Exception as e:
        logger.error(f"Error deleting channel: {e}")
        await callback.answer("❌ Помилка при видаленні каналу")

async def cancel_delete_channel(callback: CallbackQuery, button: Button, manager: DialogManager):
    await callback.answer("Видалення скасовано")
    await manager.back()