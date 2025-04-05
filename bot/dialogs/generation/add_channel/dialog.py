from aiogram.enums import ParseMode
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.kbd import Button, Row, Back, Url
from aiogram_dialog.widgets.text import Const, Format, Jinja
from aiogram_dialog.widgets.input import MessageInput

from bot.dialogs.generation.add_channel.states import AddChannelMenu 
from .getters import channel_data_getter
from .callbacks import (
    subscribe,
    on_create_flow
)
from utils.buttons import (
    go_back_to_generation
)

async def channel_success_getter(dialog_manager: DialogManager, **kwargs):
    data = dialog_manager.start_data or {}
    return {
        "channel_id": dialog_manager.start_data.get("channel_id"),
        "channel_name": dialog_manager.start_data.get("channel_name"),
        "channel_username": dialog_manager.start_data.get("channel_username")
    }

def create_add_channel_dialog():
    return Dialog(
        Window(
            Jinja(
                "📝 <b>Інструкція з додавання бота до каналу</b>\n\n"
                "<b>1. Додайте <a href='{{bot_url}}'>@{{bot_username}}</a> як адміністратора</b>\n\n"
                "<b>2. Надайте боту такі права:\n"
                "   • Надсилання повідомлень\n"
                "   • Редагування повідомлень\n"
                "   • Управління чатом</b>\n\n"
                "<b>3. Натисніть кнопку 'Перевірити права'</b>"
            ),
            Row(
                Url(
                    text=Const("📲 Додати бота автоматично"),
                    url=Jinja("{{bot_url}}")
                ),
            ),
            Row(
                Button(Const("🔙 Назад"), id="go_back_to_generation", on_click=go_back_to_generation),
            ),
            state=AddChannelMenu.instructions,
            parse_mode=ParseMode.HTML,
            getter=channel_data_getter
        ),
        Window(
            Format(
                "🎉 <b>Дякуємо! Канал {channel_name} успішно доданий.</b>\n\n"
                "ID каналу: <code>{channel_id}</code>\n"
                "Наразі вам доступна обмежена безкоштовна підписка.\n"
                "Для розширення функціоналу підпишіться на платну версію"
            ),
            Row(
                Button(Const("⚡ Створити флоу"), id="on_create_flow", on_click=on_create_flow),
                Button(Const("💎 Оформити підписку"), id="subscribe", on_click=subscribe),
            ),
            Row(
                Button(Const("🔙 Назад"), id="back", on_click=go_back_to_generation),
            ),
            state=AddChannelMenu.success,
            parse_mode=ParseMode.HTML,
            getter=channel_success_getter
        )
    )