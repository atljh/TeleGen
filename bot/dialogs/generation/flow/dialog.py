import html
import logging
from itertools import zip_longest
from aiogram.enums import ParseMode 
from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import (
    Select, ScrollingGroup, Button, Row, Button, Group,
    StubScroll, NumberedPager, Cancel, Back, Calendar
)
from aiogram_dialog.widgets.text import Const, Format

from bot.dialogs.generation.flow.states import FlowMenu
from .getters import edit_post_getter, paging_getter, post_info_getter, send_media_album
from .callbacks import (
    back_to_post_view,
    back_to_select_type,
    confirm_schedule,
    on_back_to_posts,
    on_edit_media,
    on_edit_post,
    on_edit_text,
    on_input_time,
    on_post_info,
    on_publish_post,
    on_schedule_post,
    process_edit_input,
    select_date,
    set_time,
    show_publish_confirm,
    show_time_buttons,
    time_input_handler,
)

from aiogram_dialog.widgets.kbd import NumberedPager

def chunked(iterable, n):
    args = [iter(iterable)] * n
    return zip_longest(*args)

times = [f"{hour:02d}:{minute:02d}" for hour in range(8, 23) for minute in (0, 30)]

async def on_dialog_result(
    event, 
    manager: DialogManager, 
    result
):
    if manager.current_state() == FlowMenu.posts_list:
        if manager.dialog_data.pop("needs_refresh", False):
            manager.dialog_data.pop("all_posts", None)
            await manager.show()

def flow_dialog() -> Dialog:
    from bot.dialogs.generation.callbacks import go_back_to_channels
    
    async def on_page_changed(
        callback: CallbackQuery, 
        widget,
        manager: DialogManager, 
    ):
        data = await paging_getter(manager)
        if data["post"].get("is_album"):
            await send_media_album(manager, data["post"])
            return
        # await manager.show()
    
    return Dialog(
        Window(
            Format("{post[content_preview]}", when=lambda data, widget, manager: not data["post"].get("is_album")),
            Format("Альбом {post[images_count]} зобр.", when=lambda data, widget, manager: data["post"].get("is_album")),
            DynamicMedia("media_content", when=lambda data, widget, manager: not data["post"].get("is_album")),
            StubScroll(id="stub_scroll", pages="pages", on_page_changed=on_page_changed),
            Group(
                NumberedPager(scroll="stub_scroll"),
                width=5,
            ),
            Group(
                Button(Const("✅ Опублікувати"), id="publish_post", on_click=show_publish_confirm, when=lambda data, widget, manager: data["post"].get("content")),
                Button(Const("✏️ Редагувати"), id="edit_post", on_click=on_edit_post, when=lambda data, widget, manager: data["post"].get("content")),
                Button(Const("📅 Запланувати"), id="schedule_publish", on_click=on_schedule_post, when=lambda data, widget, manager: data["post"].get("content")),
                Button(Const("ℹ️ Пост iнфо"), id="post_info", on_click=on_post_info, when=lambda data, widget, manager: data["post"].get("content")),
                width=2
            ),
            Row(
                Button(Const("🔙 Назад"), id='go_back_to_channels', on_click=go_back_to_channels)
            ),
            getter=paging_getter,
            state=FlowMenu.posts_list,
            parse_mode=ParseMode.HTML,
        ),
        Window(
            Format(
                "<b>Інформація поста</b>\n\n"
                "<b>Статус: {status}</b>\n"
                "<b>Джерело: {source_url}</b>\n"
                "<b>Посилання: {original_link}</b>\n"
                "<b>Дата публікації: {original_date}</b>"
            ),
            Row(
                Back(Const("🔙 Назад")),
            ),
            getter=post_info_getter,
            state=FlowMenu.post_info,
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
            state=FlowMenu.edit_post,
            parse_mode="HTML"
        ),
        Window(
            Const("📅 Виберіть дату публікації:"),
            Calendar(id="calendar", on_click=select_date),
            Row(
                Button(Const("🔙 Назад"), id='on_back_to_posts', on_click=on_back_to_posts)
            ),
            state=FlowMenu.select_date,
        ),
        Window(
            Format("📅 Обрана дата: {dialog_data[scheduled_date_str]}\n"
                   "🕒 Виберіть спосіб введення часу:"),
            Row(
                Button(Const("⌨ Ввести вручну"), id="input_manually", on_click=on_input_time),
                Button(Const("🕒 Вибрати зі списку"), id="select_from_list", on_click=show_time_buttons),
            ),
            Back(Const("◀️ Змінити дату")),
            state=FlowMenu.select_type,
        ),
        Window(
            Format("📅 Обрана дата: {dialog_data[scheduled_date_str]}\n"
                   "🕒 Введіть час у форматі HH:MM"),
            MessageInput(time_input_handler),
            Back(Const("◀️ Назад")),
            state=FlowMenu.input_time,
        ),
        Window(
            Format("📅 Обрана дата: {dialog_data[scheduled_date_str]}\n"
                "🕒 Виберіть час:"),
            *[
                Row(
                    *[
                        Button(Const(time), id=f"{time.replace(':', '_')}", on_click=set_time)
                        for time in row if time
                    ]
                )
                for row in chunked(times, 4)
            ],
            Button(Const("◀️ Назад"), id='back_to_select_type', on_click=back_to_select_type),
            state=FlowMenu.select_time,
        ),
        Window(
            Format("📅 Заплановано на:\n{dialog_data[scheduled_datetime_str]}"),
            Button(Const("✅ Підтвердити"), id="confirm", on_click=confirm_schedule),
            Button(Const("◀️ Назад"), id='back_to_select_type', on_click=back_to_select_type),
            state=FlowMenu.confirm_schedule,
        ),
        Window(
            Format("{post[content_preview]}", when=lambda data, widget, manager: not data["post"].get("is_album")),
            Format("Альбом {post[images_count]} зобр.", when=lambda data, widget, manager: data["post"].get("is_album")),
            DynamicMedia("media_content", when=lambda data, widget, manager: not data["post"].get("is_album")),
            Format("Ви впевнені, що хочете опублікувати цей пост?"),
            Group(
                Button(Const("✅ Так, опублікувати"), id="confirm_publish", on_click=on_publish_post),
                Button(Const("❌ Скасувати"), id="cancel_publish", on_click=back_to_post_view),
                width=2
            ),
            state=FlowMenu.publish_confirm,
            parse_mode=ParseMode.HTML,
            getter=paging_getter,
        ),
        on_process_result=on_dialog_result
    )