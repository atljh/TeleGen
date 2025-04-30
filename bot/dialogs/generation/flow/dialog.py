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
from .getters import edit_post_getter, paging_getter, send_media_album
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
            Format("<b>✏️ Редагування поста</b>\n\n"
                  "\n{content}\n\n"
                  ),
            DynamicMedia("media"),
            
            Row(
                Button(Const("📝 Змінити текст"), id="edit_text"),
                Button(Const("🖼️ Змінити медіа"), id="edit_media"),
            ),
            Row(
                Button(Const("✅ Застосувати зміни"), id="apply_edit", on_click=on_apply_edit),
                Back(Const("❌ Скасувати"))
            ),
            
            getter=edit_post_getter,
            state=FlowMenu.edit_post,
            parse_mode="HTML"
        )
    )



async def on_apply_edit(callback: CallbackQuery, button: Button, manager: DialogManager):
    edited_post = {
        "content": manager.dialog_data.get("edited_content", manager.dialog_data["original_content"]),
        "media_url": manager.dialog_data.get("edited_media", manager.dialog_data["original_media"])
    }
    
    # save_post_changes(edited_post)
    
    await show_post_preview(manager, edited_post)
    await manager.dialog().switch_to(FlowMenu.posts_list)

async def show_post_preview(manager: DialogManager, post_data: dict):
    bot = manager.middleware_data['bot']
    chat_id = manager.middleware_data['event_chat'].id
    
    if post_data.get("media_url"):
        await bot.send_photo(
            chat_id=chat_id,
            photo=post_data["media_url"],
            caption=post_data["content"],
            parse_mode="HTML"
        )
    else:
        await bot.send_message(
            chat_id=chat_id,
            text=post_data["content"],
            parse_mode="HTML"
        )

