from datetime import datetime

from aiogram.enums import ParseMode
from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import (
    Back,
    Button,
    Group,
    NumberedPager,
    Row,
    Select,
    StubScroll,
)
from aiogram_dialog.widgets.link_preview import LinkPreview
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.text import Const, Format

from bot.dialogs.buffer.getters import (
    edit_post_getter,
    get_user_channels_data,
    paging_getter,
    post_info_getter,
    send_media_album,
)
from bot.dialogs.buffer.states import BufferMenu

from bot.utils.constants.buttons import BACK_BUTTON

from .callbacks import (
    back_to_post_view,
    go_back_to_channels,
    on_back_to_posts,
    on_channel_selected,
    on_edit_media,
    on_edit_post,
    on_edit_text,
    on_hide_details,
    on_post_info,
    on_publish_post,
    on_toggle_details,
    process_edit_input,
    show_publish_confirm,
)


async def on_dialog_result(event, manager: DialogManager, result):
    if manager.current_state() == BufferError.channel_main:
        if manager.dialog_data.pop("needs_refresh", False):
            manager.dialog_data.pop("all_posts", None)
            await manager.show()


async def get_buffer_data(dialog_manager: DialogManager, **kwargs):
    data = dialog_manager.start_data or {}
    dialog_data = dialog_manager.dialog_data
    dialog_manager.dialog_data["post_text"] = dialog_data.get(
        "post_text", "Текст відсутній"
    )
    return {
        "post_text": data.get("post_text")
        or dialog_data.get("post_text", "Текст відсутній"),
        "has_media": "✅" if "media" in dialog_data else "❌",
        "publish_time": dialog_data.get("publish_time", datetime.now()).strftime(
            "%d.%m.%Y %H:%M"
        ),
        "is_scheduled": (
            "🕒 Заплановано" if "publish_time" in dialog_data else "⏳ Не заплановано"
        ),
    }


def create_buffer_dialog():
    async def on_page_changed(
        callback: CallbackQuery,
        widget,
        manager: DialogManager,
    ):
        data = await paging_getter(manager)
        if data["post"].get("is_selected") and data["post"].get("is_album"):
            await send_media_album(manager, data["post"])

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
                "Тут будуть відображатися пости",
                when=lambda data, widget, manager: not data["post"].get("content"),
            ),
            Format(
                "{post[content_preview]}\n\n"
                "<b>Заплановано:</b> {post[scheduled_time]}\n"
                "{media_indicator}",
                when=lambda data, widget, manager: not data["post"].get("is_selected")
                and data["post"].get("content"),
            ),
            Format(
                "{post[full_content]}\n\n"
                "<b>Заплановано:</b> {post[scheduled_time]}\n"
                "{media_indicator}",
                when=lambda data, widget, manager: data["post"].get("is_selected"),
            ),
            DynamicMedia(
                "media_content",
                when=lambda data, widget, manager: data["post"].get("is_selected")
                and not data["post"].get("is_album"),
            ),
            StubScroll(
                id="stub_scroll", pages="pages", on_page_changed=on_page_changed
            ),
            Group(
                NumberedPager(scroll="stub_scroll"),
                width=5,
            ),
            Group(
                Button(
                    Const("👀 Деталi"),
                    id="toggle_details",
                    on_click=on_toggle_details,
                    when=lambda data, widget, manager: not data["post"].get(
                        "is_selected"
                    )
                    and data["post"].get("content"),
                ),
                Button(
                    Const("📋 Сховати"),
                    id="hide_details",
                    on_click=on_hide_details,
                    when=lambda data, widget, manager: data["post"].get("is_selected")
                    and data["post"].get("content"),
                ),
                Button(
                    Const("✅ Опублікувати"),
                    id="publish_post",
                    on_click=show_publish_confirm,
                    when=lambda data, widget, manager: data["post"].get("content"),
                ),
                Button(
                    Const("✏️ Редагувати"),
                    id="edit_post",
                    on_click=on_edit_post,
                    when=lambda data, widget, manager: data["post"].get("content"),
                ),
                Button(
                    Const("ℹ️ Пост iнфо"),
                    id="post_info",
                    on_click=on_post_info,
                    when=lambda data, widget, manager: data["post"].get("content"),
                ),
                width=2,
            ),
            Row(
                Button(
                    BACK_BUTTON,
                    id="go_back_to_channels",
                    on_click=go_back_to_channels,
                )
            ),
            getter=paging_getter,
            state=BufferMenu.channel_main,
            parse_mode=ParseMode.HTML,
        ),
        Window(
            Format(
                "<b>Інформація поста</b>\n\n"
                "<b>Статус: {status}</b>\n"
                "<b>Джерело: {source_url}</b>\n"
                "<b>Посилання: {original_link}</b>\n"
                "<b>Дата публікації: {original_date}</b>\n\n"
                "<b>Заплановано на: {scheduled_time}</b>"
            ),
            Row(
                Back(BACK_BUTTON),
            ),
            LinkPreview(is_disabled=True),
            getter=post_info_getter,
            state=BufferMenu.post_info,
            parse_mode=ParseMode.HTML,
        ),
        Window(
            Format("<b>✏️ Редагування поста</b>\n\n\n{content}\n\n"),
            DynamicMedia("media"),
            Row(
                Button(
                    Const("📝 Змінити текст"), id="edit_text", on_click=on_edit_text
                ),
                Button(
                    Const("🖼️ Змінити медіа"), id="edit_media", on_click=on_edit_media
                ),
            ),
            Row(
                Button(
                    BACK_BUTTON, id="on_back_to_posts", on_click=on_back_to_posts
                )
            ),
            MessageInput(process_edit_input),
            getter=edit_post_getter,
            state=BufferMenu.edit_post,
            parse_mode="HTML",
        ),
        Window(
            Format(
                "{post[content_preview]}",
                when=lambda data, widget, manager: not data["post"].get("is_album"),
            ),
            Format(
                "Альбом {post[images_count]} зобр.",
                when=lambda data, widget, manager: data["post"].get("is_album"),
            ),
            DynamicMedia(
                "media_content",
                when=lambda data, widget, manager: not data["post"].get("is_album"),
            ),
            Format("\n\nВи впевнені, що хочете опублікувати цей пост?"),
            Group(
                Button(
                    Const("✅ Так, опублікувати"),
                    id="confirm_publish",
                    on_click=on_publish_post,
                ),
                Button(
                    Const("❌ Скасувати"),
                    id="cancel_publish",
                    on_click=back_to_post_view,
                ),
                width=2,
            ),
            state=BufferMenu.publish_confirm,
            parse_mode=ParseMode.HTML,
            getter=paging_getter,
        ),
        on_process_result=on_dialog_result,
    )
