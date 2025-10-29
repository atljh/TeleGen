from datetime import datetime

from aiogram_dialog import DialogManager

from bot.containers import Container


async def get_user_channels_data(dialog_manager: DialogManager, **kwargs):
    channel_service = Container.channel_service()
    user_telegram_id = dialog_manager.event.from_user.id
    channels = await channel_service.get_user_channels(user_telegram_id)
    dialog_manager.dialog_data["channels"] = channels or []
    return {"channels": channels or []}


async def selected_channel_getter(dialog_manager: DialogManager, **kwargs):
    start_data = dialog_manager.start_data or {}
    dialog_data = dialog_manager.dialog_data or {}

    selected_channel = start_data.get("selected_channel") or dialog_data.get(
        "selected_channel"
    )
    channel_flow = start_data.get("channel_flow", False) or dialog_data.get(
        "channel_flow", False
    )

    if not selected_channel:
        return {
            "channel_name": "Канал не вибрано",
            "channel_id": "N/A",
            "created_at": datetime.now(),
            "channel_flow": "Вiдсутнiй",
            "has_flow": False,
            "no_flow": True,
            "telegram_posts": 0,
            "web_posts": 0,
            "total_posts": 0,
        }

    dialog_manager.dialog_data["selected_channel"] = selected_channel
    dialog_manager.dialog_data["channel_flow"] = channel_flow

    has_flow = bool(channel_flow)

    # Count posts by source type if flow exists
    telegram_posts = 0
    web_posts = 0
    total_posts = 0

    if has_flow and channel_flow:
        from admin_panel.models import Post
        from asgiref.sync import sync_to_async

        # Get all draft posts for this flow
        posts = await sync_to_async(list)(
            Post.objects.filter(flow_id=channel_flow.id, status=Post.DRAFT)
        )
        total_posts = len(posts)

        # Count by source type
        for post in posts:
            if post.source_url and "t.me" in post.source_url:
                telegram_posts += 1
            else:
                web_posts += 1

    return {
        "channel_name": selected_channel.name,
        "channel_id": selected_channel.channel_id,
        "created_at": selected_channel.created_at,
        "channel_flow": "Присутнiй" if has_flow else "Вiдсутнiй",
        "has_flow": has_flow,
        "no_flow": not has_flow,
        "telegram_posts": telegram_posts,
        "web_posts": web_posts,
        "total_posts": total_posts,
    }
