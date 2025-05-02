import logging
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
from .getters import edit_post_getter, paging_getter, send_media_album
from .callbacks import (
    on_back_to_posts,
    on_edit_media,
    on_edit_post,
    on_edit_text,
    on_publish_post,
    on_schedule_post,
    open_calendar,
    process_edit_input,
    schedule_post,
)

from aiogram_dialog.widgets.kbd import NumberedPager

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
            Format("<b>{post[status]} | {post[created_time]}\n</b>"),
            Format("{post[content_preview]}", when=lambda data, widget, manager: not data["post"].get("is_album")),
            DynamicMedia("media_content", when=lambda data, widget, manager: not data["post"].get("is_album")),
            StubScroll(id="stub_scroll", pages="pages", on_page_changed=on_page_changed),
            Group(
                NumberedPager(scroll="stub_scroll"),
                width=5,
            ),
            Group(
                Button(Const("✅ Опублікувати"), id="publish_post", on_click=on_publish_post),
                Button(Const("✏️ Редагувати"), id="edit_post", on_click=on_edit_post),
                Button(Const("📅 Запланувати"), id="schedule_publish", on_click=open_calendar),
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
            Calendar(id="calendar", on_click=schedule_post),
            Row(
                Back(Const("◀️ Скасувати")),
            ),
            state=FlowMenu.schedule,
        ),
        on_process_result=on_dialog_result 
    )



