
from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.kbd import Select, ScrollingGroup, Button, Row, Button, Group
from aiogram_dialog.widgets.kbd import StubScroll, NumberedPager, Cancel
from aiogram_dialog.widgets.text import Const, Format
from aiogram.enums import ParseMode 
from aiogram_dialog import DialogManager
from django.conf import settings

from .getters import paging_getter
# from .paging_getter import paging_getter

from .states import FlowMenu
from .callbacks import (
    on_edit_post,
    on_publish_post,
    on_save_to_buffer,
    on_schedule_post
)


# def flow_dialog() -> Dialog:
#     return Dialog(
#         Window(
#             Const("📄 Посты для публикации:\n"),
#             DynamicMedia("media"),
#             Format("<b>{post[content_preview]}</b>\n\n"
#                    "<b>Дата:</b> {post[pub_time]}\n"
#                    "<b>Статус:</b> {post[status]}\n\n"
#                    "<i>Пост {current_page} из {pages}</i>"),
#             StubScroll(id="stub_scroll", pages="pages"),
#             NumberedPager(scroll="stub_scroll"),
#             Group(
#                 Button(Const("✅ Опублікувати"), id="publish_post", on_click=on_publish_post),
#                 Button(Const("✏️ Редагувати"), id="edit_post", on_click=on_edit_post),
#                 Button(Const("📅 Запланувати"), id="schedule_post", on_click=on_schedule_post),
#                 width=2
#             ),
#             Cancel(Const("🔙 Назад")),
#             getter=paging_getter,
#             state=FlowMenu.posts_list,
#             parse_mode=ParseMode.HTML,
#         )
#     )
def flow_dialog() -> Dialog:
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
            Cancel(Const("🔙 Назад")),
            getter=paging_getter,
            state=FlowMenu.posts_list,
            parse_mode=ParseMode.HTML,
        )
    )
