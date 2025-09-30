import logging
import os
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

import pytz
from aiogram_dialog import DialogManager
from aiogram_dialog.api.entities import MediaAttachment
from aiogram_dialog.widgets.kbd import StubScroll
from asgiref.sync import sync_to_async
from django.utils import timezone

from bot.containers import Container
from bot.database.models import PostStatus

from .utils import get_media_path, send_media_album

logger = logging.getLogger(__name__)


def format_datetime(value: Any) -> str:
    if not value:
        return "Без дати"

    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))

    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=ZoneInfo("UTC"))
        kyiv_tz = ZoneInfo("Europe/Kiev")
        value = value.astimezone(kyiv_tz)
        return value.strftime("%d.%m.%Y %H:%M")

    return "Без дати"


async def safe_format(post, field: str, default: str = "Без дати") -> str:
    value = getattr(post, field, None)
    if not value:
        return default
    return await sync_to_async(format_datetime)(value)


async def get_post_images(post) -> list:
    if hasattr(post, "images"):
        return await sync_to_async(list)(post.images)
    return []


def build_media_info(post: dict) -> dict | None:
    images = post.get("images", [])
    videos = post.get("videos", [])

    if images and len(images) == 1 and hasattr(images[0], "url"):
        return {
            "type": "photo",
            "url": images[0].url,
            "path": get_media_path(images[0].url),
        }
    if videos and len(videos) == 1 and hasattr(videos[0], "url"):
        return {
            "type": "video",
            "url": videos[0].url,
            "path": get_media_path(videos[0].url),
        }

    return None


async def build_post_dict(post, idx: int) -> dict:
    images = await get_post_images(post)
    videos = getattr(post, "videos", None)
    content = getattr(post, "content", "")

    post_stats = {
        PostStatus.DRAFT: "Чернетка",
        PostStatus.SCHEDULED: "Заплановано",
        PostStatus.PUBLISHED: "Опублiковано",
    }

    return {
        "id": str(getattr(post, "id", "")),
        "idx": idx,
        "content": content,
        "pub_time": await safe_format(post, "publication_date"),
        "created_time": await safe_format(post, "created_at"),
        "status": post_stats.get(post.status, "Невідомо"),
        "has_media": bool(images or videos),
        "images_count": len(images),
        "images": images,
        "videos": videos,
        "is_album": len(images) > 1,
        "original_date": format_datetime(getattr(post, "original_date", "")),
        "original_link": getattr(post, "original_link", ""),
        "scheduled_time": format_datetime(getattr(post, "scheduled_time", "")),
        "source_url": getattr(post, "source_url", ""),
        "content_preview": content,
        "full_content": content,
        "is_selected": False,
    }


async def get_user_channels_data(dialog_manager: DialogManager, **kwargs):
    channel_service = Container.channel_service()
    user_telegram_id = dialog_manager.event.from_user.id
    channels = await channel_service.get_user_channels(user_telegram_id)
    dialog_manager.dialog_data["channels"] = channels or []
    return {"channels": channels or []}


async def paging_getter(dialog_manager: DialogManager, **kwargs) -> dict[str, Any]:
    scroll: StubScroll = dialog_manager.find("stub_scroll")
    current_page = await scroll.get_page() if scroll else 0

    dialog_data = dialog_manager.dialog_data or {}
    start_data = dialog_manager.start_data or {}

    flow = start_data.get("channel_flow") or dialog_data.get("channel_flow")
    selected_channel = dialog_data.get("selected_channel") or start_data.get(
        "selected_channel"
    )

    dialog_manager.dialog_data.update(
        {"selected_channel": selected_channel, "channel_flow": flow}
    )

    default_data = {
        "media_indicator": "",
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
            raw_posts = await post_service.get_all_posts_in_flow(
                flow.id, status=PostStatus.SCHEDULED
            )
            dialog_data["all_posts"] = [
                await build_post_dict(post, idx) for idx, post in enumerate(raw_posts)
            ]
            dialog_data["total_posts"] = len(dialog_data["all_posts"])
        except Exception as e:
            logging.error(f"Помилка завантаження постів: {e!s}")

    posts = dialog_data.get("all_posts", [])
    total_pages = len(posts)

    dialog_manager.dialog_data["current_page"] = current_page
    if not posts or current_page >= total_pages:
        return default_data | {"selected_channel": selected_channel}

    post = posts[current_page].copy()
    selected_post_id = dialog_data.get("selected_post_id")

    if post.get("is_album"):
        media_indicator = f"📷 Альбом ({post['images_count']} фото)"
    elif post.get("images") and len(post["images"]) == 1:
        media_indicator = "🖼️ 1 фото"
    elif post.get("videos"):
        media_indicator = "🎥 Відео"
    elif post.get("has_media"):
        media_indicator = "📎 Медіа"
    else:
        media_indicator = ""

    if selected_post_id and str(post["id"]) == str(selected_post_id):
        post["is_selected"] = True
        post["content_preview"] = post["full_content"]

    data = default_data | {
        "current_page": current_page + 1,
        "pages": total_pages,
        "post": post,
        "media_indicator": media_indicator,
        "selected_channel": selected_channel,
    }

    if post["is_selected"]:
        if post.get("is_album"):
            await send_media_album(dialog_manager, post)
        else:
            media_info = build_media_info(post)
            if (
                media_info
                and media_info.get("path")
                and os.path.exists(media_info["path"])
            ):
                data["media_content"] = MediaAttachment(
                    path=media_info["path"], type=media_info["type"]
                )
            elif media_info and media_info.get("url"):
                data["media_content"] = MediaAttachment(
                    url=media_info["url"], type=media_info["type"]
                )

    return data


async def edit_post_getter(dialog_manager: DialogManager, **kwargs) -> dict[str, Any]:
    post = dialog_manager.dialog_data.get("editing_post", {}) or {}
    content = dialog_manager.dialog_data.get("edited_content", post.get("content", ""))
    edited_media = dialog_manager.dialog_data.get("edited_media")
    media_info = None

    images = post.get("images", [])
    videos = post.get("videos", [])

    if images and len(images) == 1:
        first_image = images[0]
        image_url = getattr(first_image, "url", None)
        if image_url:
            media_info = {
                "type": "photo",
                "url": image_url,
                "path": get_media_path(image_url),
            }
    if videos and len(videos) == 1:
        first_video = videos[0]
        video_url = getattr(first_video, "url", None)
        if video_url:
            media_info = {
                "type": "video",
                "url": video_url,
                "path": get_media_path(video_url),
            }

    media: MediaAttachment | None = None
    if media_info and media_info.get("path") and os.path.exists(media_info["path"]):
        media = MediaAttachment(path=media_info["path"], type=media_info["type"])
    elif media_info and media_info.get("url"):
        media = MediaAttachment(url=media_info["url"], type=media_info["type"])
    elif edited_media:
        media_path = get_media_path(edited_media["url"])
        media = MediaAttachment(path=media_path, type=edited_media["type"])

    return {"post": post, "content": content, "media": media}


async def post_info_getter(dialog_manager: DialogManager, **kwargs) -> dict[str, Any]:
    dialog_data = await paging_getter(dialog_manager)
    post = dialog_data["post"]

    original_date = post.get("original_date", "")
    kiev_date = ""

    if original_date:
        try:
            if isinstance(original_date, str):
                dt = timezone.datetime.fromisoformat(original_date)
                if not timezone.is_aware(dt):
                    dt = timezone.make_aware(dt, timezone.utc)
            elif isinstance(original_date, datetime) and not timezone.is_aware(
                original_date
            ):
                dt = timezone.make_aware(original_date, timezone.utc)
            elif isinstance(original_date, datetime):
                dt = original_date
            else:
                raise ValueError("Unsupported date format")

            kiev_tz = pytz.timezone("Europe/Kiev")
            kiev_date = timezone.localtime(dt, timezone=kiev_tz).strftime(
                "%Y-%m-%d %H:%M:%S"
            )

        except Exception as e:
            logger.debug("Error converting date: %s", e, exc_info=True)
            kiev_date = original_date

    return {
        "status": post.get("status", ""),
        "source_url": post.get("source_url", ""),
        "original_link": post.get("original_link", ""),
        "original_date": kiev_date or original_date,
    }


async def edit_schedule_getter(
    dialog_manager: DialogManager, **kwargs
) -> dict[str, Any]:
    post_data = dialog_manager.dialog_data.get("editing_post", {})

    current_schedule = post_data.get("scheduled_time", "Не заплановано")

    updated_schedule = dialog_manager.dialog_data.get("updated_schedule")
    if updated_schedule:
        current_schedule = updated_schedule

    return {"current_schedule": current_schedule, "post": post_data}
