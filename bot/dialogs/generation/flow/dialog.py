
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.kbd import Select, ScrollingGroup, Button, Row, Button, Group
from aiogram_dialog.widgets.kbd import StubScroll, NumberedPager, Cancel
from aiogram_dialog.widgets.text import Const, Format
from aiogram.enums import ParseMode 
from aiogram_dialog import DialogManager
from django.conf import settings

from .states import FlowMenu
from .getters import paging_getter
from .callbacks import (
    on_edit_post,
    on_publish_post,
    on_save_to_buffer,
    on_schedule_post
)

def flow_dialog() -> Dialog:
    from bot.dialogs.generation.callbacks import go_back_to_channels
    return Dialog(
        Window(
            DynamicMedia("media_content"),
            Format("{post[status]} | {post[pub_time]}"),
            Format("{post[content_preview]}"),
            StubScroll(id="stub_scroll", pages="pages"),
            NumberedPager(scroll="stub_scroll"),
            Group(
                Button(Const("✅ Опублікувати"), id="publish_post", on_click=on_publish_post),
                Button(Const("✏️ Редагувати"), id="edit_post", on_click=on_edit_post),
                Button(Const("📅 Запланувати"), id="schedule_post", on_click=on_schedule_post),
                width=2
            ),
            Row(
                Button(Const("🔙 Назад"), id='go_back_to_channels', on_click=go_back_to_channels)
            ),
            getter=paging_getter,
            state=FlowMenu.posts_list,
            parse_mode=ParseMode.HTML,
        )
    )
