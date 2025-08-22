import logging
from datetime import datetime
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.text import Const, Format

from bot.containers import Container
from bot.dialogs.settings.callbacks import toggle_emoji, toggle_notification

async def selected_channel_getter(dialog_manager: DialogManager, **kwargs):
    start_data = dialog_manager.start_data or {}
    dialog_data = dialog_manager.dialog_data or {}
    selected_channel = (
        start_data.get("selected_channel") 
        or dialog_data.get("selected_channel")
    )
    channel_flow = (
        start_data.get("channel_flow", False)
        or dialog_data.get("channel_flow", False)
    )
    
    dialog_manager.dialog_data['selected_channel'] = selected_channel
    dialog_manager.dialog_data['channel_flow'] = channel_flow

    try:
        return {
            "selected_channel": selected_channel,
            "channel_flow": "Присутнiй" if channel_flow else 'Вiдсутнiй',
            "signature": channel_flow.signature if channel_flow else ''
        }
    except Exception as e:
        logging.error(f"Error getting channel data: {e}")
        return {
            "selected_channel": selected_channel,
            "channel_flow": "Присутнiй" if channel_flow else 'Вiдсутнiй'
        }
    
def notification_button_getter(manager: DialogManager, **kwargs):
    value = manager.dialog_data.get("notifications_enabled", False)
    text = "✅ Сповіщення увімкнені" if value else "❌ Сповіщення вимкнені"
    return Button(Const(text), id="toggle_notif", on_click=toggle_notification)

def emoji_button_getter(manager: DialogManager, **kwargs):
    value = manager.dialog_data.get("emoji_enabled", False)
    text = "✅ Емодзі увімкнені" if value else "❌ Емодзі вимкнені"
    return Button(Const(text), id="toggle_emoji", on_click=toggle_emoji)

async def timezone_getter(dialog_manager: DialogManager, **kwargs):
    channel = dialog_manager.dialog_data["selected_channel"]
    return {
        "current_timezone": getattr(channel, "timezone", "UTC"),
        "channel_name": channel.name
    }

async def notification_getter(dialog_manager: DialogManager, **kwargs):
    channel = dialog_manager.dialog_data["selected_channel"]
    notifications_enabled = dialog_manager.dialog_data.get('notifications_enabled', False)
    return {
        "notifications_enabled": '🟢 Сповіщення увімкнено' if notifications_enabled else '🔴 Сповіщення вимкнено',
        "channel_name": channel.name
    }

async def emoji_getter(dialog_manager: DialogManager, **kwargs):
    channel = dialog_manager.dialog_data["selected_channel"]
    return {
        "emoji_enabled": getattr(channel, "emoji_enabled", False),
        "channel_name": channel.name
    }
