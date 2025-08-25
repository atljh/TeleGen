import re
import logging
from html import escape as escape_html

from aiogram.types import CallbackQuery, Message
from aiogram.enums import ParseMode

from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog import DialogManager, StartMode, Dialog, Window
from aiogram_dialog import Window, DialogManager
from aiogram_dialog.widgets.kbd import Back, Button, Column, Row

from bot.containers import Container
from bot.utils.formatting import parse_entities_to_html
from .states import SettingsMenu

logger = logging.getLogger(__name__)


async def on_channel_selected(
    callback: CallbackQuery,
    widget,
    manager: DialogManager,
    item_id: str
):
    try:
        channel_id = int(item_id)

        channel_service = Container.channel_service()
        
        selected_channel = await channel_service.get_channel_by_db_id(channel_id)

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

async def open_settings(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(SettingsMenu.channel_main_settings)


# ================== ОБРАБОТЧИКИ ОСНОВНЫХ НАСТРОЕК КАНАЛА ==================

async def open_notification_settings(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(SettingsMenu.notification_settings)

async def open_timezone_settings(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(SettingsMenu.timezone_settings)

async def open_emoji_settings(callback: CallbackQuery, button: Button, manager: DialogManager):
    # await manager.switch_to(SettingsMenu.emoji_settings)
    await callback.answer("Функція в розробці")
# ================== GETTER ДЛЯ ОКНА НАСТРОЕК ==================

async def selected_channel_getter(dialog_manager: DialogManager, **kwargs):
    channel_service = Container.channel_service()
    selected_channel_id = dialog_manager.dialog_data["selected_channel"].id
    
    try:
        channel = await channel_service.get_channel_by_db_id(selected_channel_id)
        
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
        await channel_service.delete_channel(selected_channel.channel_id)
    
        bot = manager.middleware_data["bot"]
        try:
            await bot.leave_chat(chat_id=selected_channel.channel_id)
        except Exception as leave_error:
            logger.warning(f"Couldn't leave channel {selected_channel.channel_id}: {leave_error}")
        
        await callback.message.answer("✅ Канал успішно видалено!")
        await manager.switch_to(SettingsMenu.main)
    except Exception as e:
        logger.error(f"Error deleting channel: {e}")
        await callback.answer("❌ Помилка при видаленні каналу")

async def cancel_delete_channel(callback: CallbackQuery, button: Button, manager: DialogManager):
    await callback.answer("Видалення скасовано")
    await manager.switch_to(SettingsMenu.channel_main_settings)

# ================== ОБРАБОТЧИКИ ПОДПИСИ КАНАЛА ==================

async def open_signature_editor(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(SettingsMenu.edit_signature)


async def handle_sig_input(message: Message, dialog: Dialog, manager: DialogManager):
    try:
        new_signature = parse_entities_to_html(message)

        if len(new_signature) > 200:
            await message.answer(
                "⚠️ <b>Підпис занадто довгий</b>\nМаксимум 200 символів",
                parse_mode=ParseMode.HTML
            )
            return

        flow_service = Container.flow_service()
        flow = manager.dialog_data["channel_flow"]
        await flow_service.update_flow(flow.id, signature=new_signature)
        flow.signature = new_signature

        await message.answer(
            f"✅ <b>Підпис оновлено:</b>\n{new_signature}",
            parse_mode=ParseMode.HTML
        )
        await manager.switch_to(SettingsMenu.channel_main_settings)

    except Exception as e:
        logging.error(f"Signature processing error: {str(e)}")
        await message.answer(
            "⚠️ <b>Помилка!</b> Не вдалось обробити підпис",
            parse_mode=ParseMode.HTML
        )


def escape_markdown(text: str) -> str:
    to_escape = r"_*[]()~`>#+-=|{}.!"
    return ''.join(f"\\{c}" if c in to_escape else c for c in text)


def escape_markdown_except_links(text: str) -> str:
    def escape(s):
        to_escape = r"_*[]()~`>#+-=|{}.!"
        return ''.join(f"\\{c}" if c in to_escape else c for c in s)

    parts = re.split(r"(\[[^\]]+\]\([^)]+\))", text)
    escaped = [escape(part) if not part.startswith('[') else part for part in parts]
    return ''.join(escaped)

# ================== ОБРОБНИКИ ТА GETTERS ==================

async def toggle_notification(callback: CallbackQuery, widget, manager: DialogManager):
    channel_service = Container.channel_service()
    channel = manager.dialog_data["selected_channel"]
    notifications_enabled = manager.dialog_data.get('notifications_enabled', False)
    notifications_enabled = not notifications_enabled
    manager.dialog_data['notifications_enabled'] = notifications_enabled
    await channel_service.update_channel(
        channel_id=channel.id,
        notifications=notifications_enabled
    )
    channel.notifications = notifications_enabled
    await callback.answer(f"Сповіщення {'увімкнені' if notifications_enabled else 'вимкнені'}")

async def set_timezone(callback: CallbackQuery, button: Button, manager: DialogManager):
    tz_mapping = {
        "europe_kiev": "Europe/Kiev",
        "europe_london": "Europe/London",
        "america_new_york": "America/New_York"
    }
    
    tz_key = button.widget_id.replace("tz_", "")
    tz = tz_mapping.get(tz_key)
    
    if not tz:
        await callback.answer("Невідомий часовий пояс")
        return
    
    channel_service = Container.channel_service()
    channel = manager.dialog_data["selected_channel"]
    
    await channel_service.update_channel(
        channel_id=channel.id,
        timezone=tz
    )
    
    display_names = {
        "Europe/Kiev": "🇺🇦 Київ (UTC+2)",
        "Europe/London": "🇪🇺 Лондон (UTC+0)",
        "America/New_York": "🇺🇸 Нью-Йорк (UTC-4)"
    }
    
    await callback.answer(f"Часовий пояс встановлено: {display_names[tz]}")
    await manager.switch_to(SettingsMenu.channel_main_settings)

async def toggle_emoji(callback: CallbackQuery, widget, manager: DialogManager, is_enabled: bool):
    channel_service = Container.channel_service()
    channel = manager.dialog_data["selected_channel"]
    
    await channel_service.update_channel(
        channel_id=channel.id,
        emoji_enabled=is_enabled
    )
    channel.emoji_enabled = is_enabled
    await callback.answer(f"Емодзі {'увімкнені' if is_enabled else 'вимкнені'}")



