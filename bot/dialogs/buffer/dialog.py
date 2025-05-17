from aiogram_dialog import Dialog, Window
from aiogram.enums import ParseMode 
from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, Row, Column, Back, Calendar
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.input import TextInput, MessageInput
from aiogram_dialog.widgets.kbd import (
    Select, ScrollingGroup, Button, Row, Button, Group,
    StubScroll, NumberedPager, Cancel, Back, Calendar
)
from aiogram.enums import ParseMode

from aiogram_dialog import DialogManager

from datetime import datetime, timedelta

from bot.dialogs.buffer.getters import (
    edit_post_getter, get_user_channels_data,
    paging_getter, post_info_getter, send_media_album
)

from bot.dialogs.buffer.states import BufferMenu
from .callbacks import (
    go_back_to_channels,
    on_back_to_posts,
    on_channel_selected,
    on_edit_media,
    on_edit_post,
    on_edit_text,
    on_post_info,
    on_publish_post,
    process_edit_input,
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
    async def on_page_changed(
        callback: CallbackQuery, 
        widget,
        manager: DialogManager, 
    ):
        data = await paging_getter(manager)
        if data["post"].get("is_album"):
            await send_media_album(manager, data["post"])
            return

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
            Format("{post[content_preview]}", when=lambda data, widget, manager: not data["post"].get("is_album")),
            Format("|", when=lambda data, widget, manager: data["post"].get("is_album")),
            DynamicMedia("media_content", when=lambda data, widget, manager: not data["post"].get("is_album")),
            StubScroll(id="stub_scroll", pages="pages", on_page_changed=on_page_changed),
            Group(
                NumberedPager(scroll="stub_scroll"),
                width=5,
            ),
            Group(
                Button(Const("✅ Опублікувати"), id="publish_post", on_click=on_publish_post, when=lambda data, widget, manager: data["post"].get("content")),
                Button(Const("✏️ Редагувати"), id="edit_post", on_click=on_edit_post, when=lambda data, widget, manager: data["post"].get("content")),
                Button(Const("ℹ️ Пост iнфо"), id="post_info", on_click=on_post_info, when=lambda data, widget, manager: data["post"].get("content")),
                width=2
            ),
            Row(
                Button(Const("🔙 Назад"), id='go_back_to_channels', on_click=go_back_to_channels)
            ),
            getter=paging_getter,
            state=BufferMenu.channel_main,
            parse_mode=ParseMode.HTML,
        ),
        Window(
            Format(
                "<b>Інформація поста</b>\n\n"
                "<b>Статус:</b> {status}\n"
                "<b>Джерело:</b> {source_url}\n"
                "<b>Посилання:</b> {original_link}\n"
                "<b>Дата публікації:</b> {original_date}"
            ),
            Row(
                Back(Const("🔙 Назад")),
            ),
            getter=post_info_getter,
            state=BufferMenu.post_info,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        ),
        Window(
            Format("<b>✏️ Редагування поста</b>\n\n"
                "\n{content}\n\n"
                ),
            DynamicMedia("media"),
            
            Row(
                Button(Const("📝 Змінити текст"), id="edit_text", on_click=on_edit_text),
                Button(Const("🖼️ Змінити медіа"), id="edit_media", on_click=on_edit_media),
            ),
            Row(
                Button(Const("🔙 Назад"), id='on_back_to_posts', on_click=on_back_to_posts)
            ),
            
            MessageInput(process_edit_input),
            
            getter=edit_post_getter,
            state=BufferMenu.edit_post,
            parse_mode="HTML"
        ),
    )
