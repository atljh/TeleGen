from aiogram.enums import ParseMode
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Button, Row, Back
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.kbd import Url
from aiogram_dialog.widgets.text import Jinja

from .states import AddChannelMenu

from .getters import channel_data_getter

def create_add_channel_dialog():
    return Dialog(
        Window(
            Format(
                "📝 <b>Інструкція з додавання бота в канал</b>\n\n"
                "1. Додайте бота @{bot_username} як адміністратора каналу\n"
                "2. Надайте боту наступні права:\n"
                "   - Надсилання повідомлень\n"
                "   - Редагування повідомлень\n"
                "   - Додавання медіа\n\n"
                "3. Після налаштування натисніть кнопку 'Перевірити права'"
            ),
            Row(
                Url(
                    text=Const("📲 Додати бота в канал"),
                    url=Jinja("{{bot_url}}")
                ),
                Button(Const("✅ Перевірити права"), id="check_permissions"),
            ),
            Back(Const("🔙 Назад")),
            state=AddChannelMenu.instructions,
            parse_mode=ParseMode.HTML,
            getter=channel_data_getter
        ),
        Window(
            Format(
                "🔍 <b>Перевірка прав</b>\n\n"
                "{result}\n\n"
                "Якщо все правильно - можете починати роботу!"
            ),
            Back(Const("🔙 Назад")),
            state=AddChannelMenu.check_permissions,
            parse_mode=ParseMode.HTML
        )
    )