import logging
from aiogram.enums import ParseMode
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.kbd import Button, Row, Back, Url
from aiogram_dialog.widgets.text import Const, Format, Jinja
from aiogram_dialog.widgets.input import MessageInput

from bot.containers import Container
from bot.dialogs.generation.add_channel.states import AddChannelMenu
from .getters import channel_data_getter
from .callbacks import check_admin_rights, subscribe, on_create_flow
from utils.buttons import go_back_to_generation


async def channel_success_getter(dialog_manager: DialogManager, **kwargs):
    channel_id = dialog_manager.start_data.get("channel_id")
    channel_service = Container.channel_service()
    channel = await channel_service.get_channel_by_telegram_id(channel_id)
    dialog_manager.dialog_data["selected_channel"] = channel
    return {
        "channel_id": channel_id,
        "channel_name": dialog_manager.start_data.get("channel_name"),
        "channel_username": dialog_manager.start_data.get("channel_username"),
    }


def create_add_channel_dialog():
    return Dialog(
        Window(
            Format(
                "📝 *Інструкція з додавання бота до каналу*\n\n"
                "> Додайте канал, натиснувши на кнопку нижче👇\n\n",
                when=lambda data, widget, manager: not data.get("is_admin"),
            ),
            Format(
                "✅ <b>Ви вже додали бота до цього каналу!</b>\n\n"
                "<b>ID каналу:</b> {channel_id}\n"
                "<b>Назва:</b> {channel_name}",
                when=lambda data, widget, manager: data.get("is_admin"),
            ),
            Row(
                Url(text=Const("📲 Додати бота автоматично"), url=Jinja("{{bot_url}}")),
            ),
            Row(
                Button(Const("🔙 Назад"), id="go_back", on_click=go_back_to_generation),
            ),
            parse_mode=ParseMode.MARKDOWN_V2,
            state=AddChannelMenu.instructions,
            getter=channel_data_getter,
        ),
        Window(
            Format(
                "🎉 <b>Канал {channel_name} успішно доданий!</b>\n\n"
                "ID каналу: {channel_id}\n"
                "Тепер ви можете створювати автоматичні публікації.",
            ),
            Row(
                Button(
                    Const("⚡ Створити флоу"), id="create_flow", on_click=on_create_flow
                ),
                Button(Const("💎 Підписатися"), id="subscribe", on_click=subscribe),
            ),
            Row(
                Button(Const("🔙 Назад"), id="back", on_click=go_back_to_generation),
            ),
            parse_mode=ParseMode.HTML,
            state=AddChannelMenu.success,
            getter=channel_success_getter,
        ),
    )
