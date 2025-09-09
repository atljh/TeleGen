import logging
import os
from datetime import datetime
from functools import lru_cache
from typing import Any, Optional
from zoneinfo import ZoneInfo

from aiogram.types import (
    FSInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    Message,
)
from aiogram_dialog import DialogManager
from aiogram_dialog.api.entities import MediaAttachment
from aiogram_dialog.widgets.kbd import StubScroll
from asgiref.sync import sync_to_async
from django.conf import settings

from bot.containers import Container
from bot.database.models import PostStatus


@lru_cache(maxsize=100)
def get_media_path(media_url: str) -> str:
    return os.path.join(settings.MEDIA_ROOT, media_url.split("/media/")[-1])


async def get_user_channels_data(dialog_manager: DialogManager, **kwargs):
    channel_service = Container.channel_service()
    user_telegram_id = dialog_manager.event.from_user.id
    channels = await channel_service.get_user_channels(user_telegram_id)
    dialog_manager.dialog_data["channels"] = channels or []
    return {"channels": channels or []}


async def send_media_album(
    dialog_manager: DialogManager, post_data: dict[str, Any]
) -> Optional[Message]:
    bot = dialog_manager.middleware_data["bot"]
    chat_id = dialog_manager.middleware_data["event_chat"].id
    message = dialog_manager.event.message

    message_ids = dialog_manager.dialog_data.get("message_ids", [])
    if message_ids:
        bot = dialog_manager.middleware_data["bot"]
        chat_id = dialog_manager.middleware_data["event_chat"].id
        for msg_id in message_ids:
            try:
                await bot.delete_message(chat_id=chat_id, message_id=msg_id)
            except:
                pass
        dialog_manager.dialog_data["message_ids"] = []

    try:
        images = post_data.get("images", [])[:10]
        if not images:
            return None

        media_group = []
        for i, image in enumerate(images):
            media_path = get_media_path(image.url)
            if not os.path.exists(media_path):
                continue

            media = InputMediaPhoto(
                media=FSInputFile(media_path),
                # caption=post_data['content'] if i == 0 else None,
                parse_mode="HTML",
            )
            media_group.append(media)

        if media_group:
            try:
                await message.delete()
            except:
                pass

            new_messages = await bot.send_media_group(
                chat_id=chat_id, media=media_group
            )
            message_ids = [msg.message_id for msg in new_messages]

            dialog_manager.dialog_data["message_ids"] = message_ids

    except Exception as e:
        logging.error(f"Error sending media album: {str(e)}")
        await dialog_manager.event.answer("⚠️ Не вдалось вiдправити альбом")

    return None


def build_album_keyboard(post_data: dict) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Опублікувати", callback_data=f"publish_{post_data['id']}"
                ),
                InlineKeyboardButton(
                    text="✏️ Редагувати", callback_data=f"edit_{post_data['id']}"
                ),
            ],
            [
                InlineKeyboardButton(text="🔙 Назад", callback_data="go_back"),
            ],
        ]
    )
    return keyboard


async def paging_getter(dialog_manager: DialogManager, **kwargs) -> dict[str, Any]:
    scroll: StubScroll = dialog_manager.find("stub_scroll")
    current_page = await scroll.get_page() if scroll else 0

    dialog_data = dialog_manager.dialog_data or {}
    start_data = dialog_manager.start_data or {}

    flow = start_data.get("channel_flow") or dialog_data.get("channel_flow")

    selected_channel = dialog_data.get("selected_channel") or start_data.get(
        "selected_channel"
    )

    dialog_manager.dialog_data["selected_channel"] = selected_channel
    dialog_manager.dialog_data["channel_flow"] = dialog_data.get("channel_flow")

    data = {
        "current_page": 1,
        "pages": 0,
        "day": "Немає постів",
        "media_content": None,
        "post": {
            "id": "",
            "idx": 0,
            "content_preview": "Тут будуть відображатися пости",
            "pub_time": "",
            "created_time": "",
            "status": "",
            "full_content": "",
            "has_media": False,
            "images_count": 0,
            "is_album": False,
            "scheduled_time": "",
            "is_selected": False,
        },
    }

    if dialog_data.pop("needs_refresh", False) or "all_posts" not in dialog_data:
        post_service = Container.post_service()
        try:
            raw_posts = await post_service.get_posts_by_flow_id(
                flow.id, status=PostStatus.SCHEDULED
            )
            posts = []
            for idx, post in enumerate(raw_posts):
                images = post.images if hasattr(post, "images") else []
                video_url = post.video_url if hasattr(post, "video_url") else None
                content = post.content if hasattr(post, "content") else ""

                original_link = (
                    post.original_link if hasattr(post, "original_link") else ""
                )
                source_url = post.source_url if hasattr(post, "source_url") else ""

                original_date = (
                    post.original_date if hasattr(post, "original_date") else ""
                )
                if original_date:
                    if isinstance(original_date, str):
                        original_date = datetime.fromisoformat(
                            original_date.replace("Z", "+00:00")
                        )
                        kyiv_tz = ZoneInfo("Europe/Kiev")
                        original_date = original_date.astimezone(kyiv_tz)
                        original_date = original_date.strftime("%d.%m.%Y %H:%M")
                    elif isinstance(original_date, datetime):
                        if original_date.tzinfo is None:
                            original_date = original_date.replace(
                                tzinfo=ZoneInfo("UTC")
                            )
                        kyiv_tz = ZoneInfo("Europe/Kiev")
                        original_date = original_date.astimezone(kyiv_tz)
                        original_date = original_date.strftime("%d.%m.%Y %H:%M")

                scheduled_time = (
                    post.scheduled_time if hasattr(post, "scheduled_time") else ""
                )
                if scheduled_time:
                    if isinstance(scheduled_time, str):
                        scheduled_time = datetime.fromisoformat(
                            scheduled_time.replace("Z", "+00:00")
                        )
                        kyiv_tz = ZoneInfo("Europe/Kiev")
                        scheduled_time = scheduled_time.astimezone(kyiv_tz)
                        scheduled_time = scheduled_time.strftime("%d.%m.%Y %H:%M")
                    elif isinstance(scheduled_time, datetime):
                        if scheduled_time.tzinfo is None:
                            scheduled_time = scheduled_time.replace(
                                tzinfo=ZoneInfo("UTC")
                            )
                        kyiv_tz = ZoneInfo("Europe/Kiev")
                        scheduled_time = scheduled_time.astimezone(kyiv_tz)
                        scheduled_time = scheduled_time.strftime("%d.%m.%Y %H:%M")

                pub_time = await sync_to_async(
                    lambda: (
                        post.publication_date.strftime("%d.%m.%Y %H:%M")
                        if hasattr(post, "publication_date") and post.publication_date
                        else "Без дати"
                    )
                )()
                created_time = await sync_to_async(
                    lambda: (
                        post.created_at.strftime("%d.%m.%Y %H:%M")
                        if hasattr(post, "created_at") and post.created_at
                        else "Без дати"
                    )
                )()
                post_stats = {
                    PostStatus.DRAFT: "Чернетка",
                    PostStatus.SCHEDULED: "Заплановано",
                    PostStatus.PUBLISHED: "Опублiковано",
                }
                is_album = len(images) > 1

                truncated_content = content[:150]
                if len(content) > 150:
                    truncated_content += "..."
                content_preview = truncated_content

                post_dict = {
                    "id": str(post.id) if hasattr(post, "id") else "",
                    "idx": idx,
                    "content": content,
                    "pub_time": pub_time,
                    "created_time": created_time,
                    "status": post_stats.get(post.status, "Невідомо"),
                    "has_media": bool(images or video_url),
                    "images_count": len(images),
                    "images": images,
                    "video_url": video_url,
                    "is_album": is_album,
                    "original_date": original_date or "Без дати",
                    "original_link": original_link,
                    "scheduled_time": scheduled_time,
                    "source_url": source_url,
                    "content_preview": content_preview,
                    "full_content": content,
                    "is_selected": False,
                }

                posts.append(post_dict)

            dialog_data["all_posts"] = posts
            dialog_data["total_posts"] = len(posts)

        except Exception as e:
            logging.error(f"Помилка завантаження постів: {str(e)}")
    else:
        posts = dialog_data.get("all_posts", [])

    total_pages = len(posts)

    selected_post_id = dialog_data.get("selected_post_id")
    dialog_manager.dialog_data["current_page"] = current_page

    if posts and current_page < total_pages:
        post = posts[current_page].copy()

        media_indicator = ""
        if post.get("is_album"):
            media_indicator = f"📷 Альбом ({post['images_count']} фото)"
        elif post.get("images") and len(post["images"]) == 1:
            media_indicator = "🖼️ 1 фото"
        elif post.get("video_url"):
            media_indicator = "🎥 Відео"
        elif post.get("has_media"):
            media_indicator = "📎 Медіа"

        if selected_post_id and str(post["id"]) == str(selected_post_id):
            post["is_selected"] = True
            post["content_preview"] = post["full_content"]
        else:
            post["is_selected"] = False

        data.update(
            {
                "current_page": current_page + 1,
                "pages": total_pages,
                "post": post,
                "media_indicator": media_indicator,
            }
        )

        messages = dialog_manager.dialog_data.get("message_ids")
        if messages and not post.get("is_album"):
            for message_id in messages:
                bot = dialog_manager.middleware_data["bot"]
                chat_id = dialog_manager.middleware_data["event_chat"].id
                try:
                    await bot.delete_message(chat_id=chat_id, message_id=message_id)
                except Exception:
                    pass
                dialog_manager.dialog_data["message_ids"] = []

        if post["is_selected"] and not post.get("is_album"):
            media_info = None
            images = post.get("images", [])

            if images and len(images) == 1:
                first_image = images[0]
                if hasattr(first_image, "url"):
                    media_info = {
                        "type": "photo",
                        "url": first_image.url,
                        "path": (
                            get_media_path(first_image.url) if first_image.url else None
                        ),
                    }
            elif post.get("video_url"):
                media_info = {
                    "type": "video",
                    "url": post["video_url"],
                    "path": get_media_path(post["video_url"]),
                }

            if (
                media_info
                and media_info.get("path")
                and os.path.exists(media_info["path"])
            ):
                data["media_content"] = MediaAttachment(
                    path=media_info["path"], type=media_info["type"]
                )
        else:
            data["media_content"] = None

    data["selected_channel"] = selected_channel
    if data["post"].get("is_selected") and data["post"].get("is_album"):
        await send_media_album(dialog_manager, data["post"])
    return data


async def edit_post_getter(dialog_manager: DialogManager, **kwargs):
    post = dialog_manager.dialog_data.get("editing_post", {})
    content = dialog_manager.dialog_data.get("edited_content", post.get("content", ""))
    edited_media = dialog_manager.dialog_data.get("edited_media")
    media_info = None
    images = post.get("images", [])
    video_url = post.get("video_url")

    if images and len(images) == 1:
        first_image = images[0]
        if hasattr(first_image, "url"):
            media_info = {
                "type": "photo",
                "url": first_image.url,
                "path": get_media_path(first_image.url) if first_image.url else None,
            }
    elif video_url:
        media_info = {
            "type": "video",
            "url": video_url,
            "path": get_media_path(video_url),
        }

    media = None
    if media_info and media_info.get("path") and os.path.exists(media_info["path"]):
        media = MediaAttachment(path=media_info["path"], type=media_info["type"])
    elif edited_media:
        media_path = get_media_path(edited_media["url"])
        media = MediaAttachment(path=media_path, type=edited_media["type"])
    return {"post": post, "content": content, "media": media}


async def post_info_getter(dialog_manager: DialogManager, **kwargs):
    dialog_data = await paging_getter(dialog_manager)
    post = dialog_data["post"]
    return {
        "status": post.get("status", ""),
        "source_url": post.get("source_url", ""),
        "original_link": post.get("original_link", ""),
        "original_date": post.get("original_date", ""),
        "scheduled_time": post.get("scheduled_time", ""),
    }
