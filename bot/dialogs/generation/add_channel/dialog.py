import logging
from aiogram.enums import ParseMode
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.kbd import Button, Row, Back, Url
from aiogram_dialog.widgets.text import Const, Format, Jinja
from aiogram_dialog.widgets.input import MessageInput

from bot.containers import Container
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
    channel_id = dialog_manager.start_data.get("channel_id")
    channel_service = Container.channel_service()
    channel = await channel_service.get_channel(channel_id)
    logging.info(channel)
    dialog_manager.dialog_data['selected_channel'] = channel
    return {
        "channel_id": channel_id,
        "channel_name": dialog_manager.start_data.get("channel_name"),
        "channel_username": dialog_manager.start_data.get("channel_username")
    }

def create_add_channel_dialog():
    return Dialog(
        Window(
            Jinja(
                "📝 **Інструкція з додавання бота до каналу**\n\n"
                "**1. Додайте <a href='{{bot_url}}'>@{{bot_username}}</a> як адміністратора**\n\n"
                "**2. Надайте боту такі права:\n"
                "   • Надсилання повідомлень\n"
                "   • Редагування повідомлень\n"
                "   • Управління чатом**\n\n"
                "**3. Натисніть кнопку 'Перевірити права'**"
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
            parse_mode=ParseMode.MARKDOWN_V2,
            getter=channel_data_getter
        ),
        Window(
            Format(
                "🎉 **Дякуємо! Канал {channel_name} успішно доданий.**\n\n"
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
            parse_mode=ParseMode.MARKDOWN_V2,
            getter=channel_success_getter
        )
    )