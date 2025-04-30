import logging
from aiogram.enums import ParseMode 
from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import (
    Select, ScrollingGroup, Button, Row, Button, Group,
    StubScroll, NumberedPager, Cancel, Back
)
from aiogram_dialog.widgets.text import Const, Format

from bot.dialogs.generation.flow.states import FlowMenu
from .getters import paging_getter, send_media_album
from .callbacks import (
    on_edit_post,
    on_publish_post,
    on_save_edited_post,
    on_schedule_post,
    process_edit_input,
)

from aiogram_dialog.widgets.kbd import NumberedPager


def flow_dialog() -> Dialog:
    from bot.dialogs.generation.callbacks import go_back_to_channels
    
    async def on_page_changed(
        callback: CallbackQuery, 
        widget,
        manager: DialogManager, 
    ):
        # manager.dialog_data["page"] = page 
        data = await paging_getter(manager)
        if data["post"].get("is_album"):
            await send_media_album(manager, data["post"])
            return
        await manager.show()
    
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
            Format("<b>Редактирование поста:</b>\n\n{editing_post[content_preview]}\n\n"
                  "<i>Отправьте новый текст сообщения...</i>"),
            MessageInput(process_edit_input),
            Row(
                Button(Const("💾 Сохранить"), id="save_edit", on_click=on_save_edited_post),
                Button(Const("❌ Отмена"), id="cancel_edit", on_click=lambda c, b, m: m.switch_to(FlowMenu.posts_list))
            ),
            state=FlowMenu.edit_post,
            getter=edit_post_getter,
            parse_mode=ParseMode.HTML
        )
    )



async def edit_post_getter(dialog_manager: DialogManager, **kwargs):
    return {
        "editing_post": dialog_manager.dialog_data.get("editing_post", {})
    }