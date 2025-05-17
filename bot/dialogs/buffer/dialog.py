from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Button, Row, Column, Back, Calendar
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.input import TextInput, MessageInput
from aiogram_dialog.widgets.kbd import Button, Row, Back, Group, Select, Column
from aiogram.enums import ParseMode

from aiogram_dialog import DialogManager

from datetime import datetime, timedelta

from .states import BufferMenu
from .callbacks import (
    publish_now,
    on_text_edited,
    open_calendar,
    schedule_post
)

async def get_buffer_data(dialog_manager: DialogManager, **kwargs):
    data = dialog_manager.start_data or {}
    dialog_data = dialog_manager.dialog_data
    dialog_manager.dialog_data["post_text"] = dialog_data.get("post_text", "Текст відсутній")
    return {
        "post_text": data.get("post_text") or dialog_data.get("post_text", "Текст відсутній"),
        "has_media": "✅" if "media" in dialog_data else "❌",
        "publish_time": dialog_data.get("publish_time", datetime.now()).strftime("%d.%m.%Y %H:%M"),
        "is_scheduled": "🕒 Заплановано" if "publish_time" in dialog_data else "⏳ Не заплановано"
    }

def create_buffer_dialog():
    return Dialog(
        Window(
            Const("Оберiть канал"),
            Group(
                Select(
                    text=Format("{item.name}"),
                    item_id_getter=lambda channel: channel.id,
                    items="channels",
                    id="channel_select",
                    on_click=on_channel_selected,
                ),
                width=2,
            ),
            state=BufferMenu.main,
            parse_mode=ParseMode.HTML,
            getter=get_user_channels_data,
        ),
        Window(
            Format(
                "📌 <b>Буфер публікацій</b>\n\n"
                "Текст: {post_text}\n"
                "Медіа: {has_media}\n"
                "Статус: {is_scheduled}\n\n"
                "Оберіть дію:"
            ),
            Row(
                Button(Const("✅ Опублікувати зараз"), id="publish_now", on_click=publish_now),
                Button(Const("📅 Запланувати"), id="schedule_publish", on_click=open_calendar),
            ),
            Row(
                Button(Const("✏️ Редагувати"), id="edit_post", on_click=on_text_edited),
                Button(Const("🗑 Видалити чернетку"), id="delete_draft"),
            ),
            state=BufferMenu.preview,
            parse_mode=ParseMode.HTML,
            getter=get_buffer_data
        ),

        Window(
            Const("📅 Виберіть дату публікації:"),
            Calendar(id="calendar", on_click=schedule_post),
            Row(
                Back(Const("◀️ Скасувати")),
            ),
            state=BufferMenu.set_schedule,
        ),
    )
