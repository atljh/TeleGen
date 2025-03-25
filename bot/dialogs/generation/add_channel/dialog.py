from aiogram.enums import ParseMode
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Button, Row, Back, Url
from aiogram_dialog.widgets.text import Const, Format, Jinja
from aiogram_dialog.widgets.input import MessageInput

from .states import AddChannelMenu
from .getters import channel_data_getter
from .callbacks import (
    check_permissions,
    process_channel_input,
    go_back_to_generation,
    go_back_to_main
)

def create_add_channel_dialog():
    return Dialog(
        Window(
            Const("✏️ Введіть @username або ID вашого каналу:"),
            Row(
                Button(Const("◀️ Назад"), id="go_back_to_generation", on_click=go_back_to_main),
            ),
            MessageInput(process_channel_input),
            state=AddChannelMenu.enter_channel_id,
            parse_mode=ParseMode.HTML
        ),
        Window(
            Jinja(
                "📝 <b>Інструкція з додавання бота до каналу</b>\n\n"
                "1. Додайте <a href='{{bot_url}}'>@{{bot_username}}</a> як адміністратора\n"
                "2. Надайте боту такі права:\n"
                "   • Надсилання повідомлень\n"
                "   • Редагування повідомлень\n"
                "   • Управління чатом\n\n"
                "3. Натисніть кнопку 'Перевірити права'"
            ),
            Row(
                Url(
                    text=Const("📲 Додати бота автоматично"),
                    url=Jinja("{{bot_url}}")
                ),
                Button(Const("✅ Перевірити права"), id="check_permissions", on_click=check_permissions),
            ),
            Row(
                Back(Const("◀️ Назад")),
                Button(Const("Головне меню"), id="go_back_to_main", on_click=go_back_to_main),
            ),
            state=AddChannelMenu.instructions,
            parse_mode=ParseMode.HTML,
            getter=channel_data_getter
        ),
        Window(
            Format("{dialog_data[result]}"),
            Row(
                Back(Const("◀️ Назад")),
                Button(Const("Головне меню"), id="go_back_to_main", on_click=go_back_to_main),
            ),
            state=AddChannelMenu.check_permissions,
            parse_mode=ParseMode.HTML
        )
    )