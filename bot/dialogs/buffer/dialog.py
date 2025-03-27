from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Button, Row, Column, Back, Calendar
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.input import TextInput, MessageInput
from aiogram.enums import ParseMode
from aiogram.types import Message, CallbackQuery, ContentType
from aiogram_dialog import DialogManager

from datetime import datetime, timedelta

from .states import BufferMenu
from .callbacks import (
    publish_now,
    on_text_edited,
    on_media_edited,
    on_calendar_selected,
    publish_immediately,
    schedule_publication
)


async def get_post_preview_data(dialog_manager: DialogManager, **kwargs):
    data = dialog_manager.dialog_data
    return {
        "post_text": data.get("post_text", "Текст відсутній"),
        "has_media": "✅" if "media" in data else "❌",
        "publish_time": data.get(
            "publish_time", 
            datetime.now()
        ).strftime("%d.%m.%Y %H:%M")
    }

def create_buffer_dialog():
    return Dialog(
        Window(
            Const(
                "📌 <b>Буфер публікацій</b>\n\n"
                "<b>Текст:</b> {post_text}\n"
                "<b>Медіа:</b> {has_media}\n"
                "<b>Час публікації:</b> {publish_time}\n\n"
                "Оберіть дію:"
            ),
            Row(
                Button(Const("✅ Опублікувати зараз"), id="publish_now", on_click=publish_now),
                Button(Const("📅 Запланувати"), id="schedule_publish", on_click=schedule_publication),
            ),
            Row(
                Button(Const("✏️ Редагувати"), id="edit_post", on_click=on_text_edited),
                Button(Const("🗑 Видалити чернетку"), id="delete_draft"),
            ),
            Row(
                Back(Const("◀️ Назад")),
            ),
            state=BufferMenu.preview,
            parse_mode=ParseMode.HTML,
            getter=get_post_preview_data
        )
    )
