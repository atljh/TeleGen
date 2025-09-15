import asyncio
import logging
import sys

from aiogram import Bot
from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager, StartMode
from aiogram_dialog.widgets.kbd import Button

from bot.containers import Container
from bot.database.models.post import PostStatus
from bot.dialogs.buffer.states import BufferMenu
from bot.dialogs.generation.add_channel.states import AddChannelMenu
from bot.dialogs.generation.create_flow.states import CreateFlowMenu
from bot.dialogs.generation.flow.states import FlowMenu
from bot.dialogs.generation.states import GenerationMenu

logger = logging.getLogger(__name__)


async def go_back_to_channels(
    callback: CallbackQuery, button: Button, manager: DialogManager
):
    channel = manager.dialog_data.get("selected_channel") or manager.start_data.get(
        "selected_channel"
    )
    channel_flow = manager.dialog_data.get("channel_flow") or manager.start_data.get(
        "channel_flow"
    )
    messages = manager.dialog_data.get("message_ids")
    bot = manager.middleware_data["bot"]

    if messages:
        for message_id in messages:
            bot = manager.middleware_data["bot"]
            chat_id = manager.middleware_data["event_chat"].id
            await bot.delete_message(chat_id=chat_id, message_id=message_id)
            manager.dialog_data["message_ids"] = []

    await manager.start(
        GenerationMenu.channel_main,
        data={
            "selected_channel": channel,
            "channel_flow": channel_flow,
            "item_id": str(channel.id),
        },
    )


async def on_channel_selected(
    callback: CallbackQuery, widget, manager: DialogManager, item_id: str
):
    try:
        data = manager.dialog_data
        channels = data.get("channels", [])
        selected_channel = next(
            (channel for channel in channels if str(channel.id) == item_id), None
        )

        if not selected_channel:
            await callback.answer("Channel not found!")
            return

        flow_service = Container.flow_service()
        channel_flow = await flow_service.get_flow_by_channel_id(int(item_id))
        manager.dialog_data["item_id"] = item_id

        manager.dialog_data.update(
            {"selected_channel": selected_channel, "channel_flow": channel_flow}
        )

        await manager.switch_to(GenerationMenu.channel_main)

    except Exception as e:
        logger.error(f"Channel selection error: {e}", exc_info=True)
        await callback.answer("Error processing selection")


async def add_channel(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.start(AddChannelMenu.instructions, mode=StartMode.RESET_STACK)


async def on_flow(callback: CallbackQuery, button: Button, manager: DialogManager):
    selected_channel = manager.dialog_data.get("selected_channel")
    channel_flow = manager.dialog_data.get("channel_flow")
    item_id = manager.dialog_data.get("item_id")

    if not channel_flow:
        await callback.answer(f"У канала {selected_channel.name} поки немає Флоу")
        return
    await manager.start(
        FlowMenu.posts_list,
        data={
            "selected_channel": selected_channel,
            "channel_flow": channel_flow,
            "channel_id": item_id,
        },
        mode=StartMode.RESET_STACK,
    )


async def on_create_flow(
    callback: CallbackQuery, button: Button, manager: DialogManager
):
    selected_channel = manager.dialog_data.get("selected_channel")
    channel_flow = manager.dialog_data.get("channel_flow")
    if channel_flow:
        await callback.answer(f"У канала {selected_channel.name} вже є Флоу")
        return
    await manager.start(
        CreateFlowMenu.select_theme,
        data={"selected_channel": selected_channel},
        mode=StartMode.RESET_STACK,
    )


async def on_buffer(callback: CallbackQuery, button: Button, manager: DialogManager):
    channel = manager.dialog_data.get("selected_channel") or manager.start_data.get(
        "selected_channel"
    )
    channel_flow = manager.dialog_data.get("channel_flow") or manager.start_data.get(
        "channel_flow"
    )

    await manager.start(
        BufferMenu.channel_main,
        data={
            "from_gen": True,
            "selected_channel": channel,
            "channel_flow": channel_flow,
            "item_id": str(channel.id),
        },
    )


async def on_force_generate(
    callback: CallbackQuery, button: Button, manager: DialogManager
):
    try:
        dialog_data = manager.dialog_data
        flow = dialog_data.get("channel_flow")

        if not flow:
            await callback.answer("⚠️ Не обрано флоу для генерації", show_alert=True)
            return

        await callback.answer("🔄 Запускаю генерацію...")

        bot = manager.middleware_data["bot"]
        status_msg = await bot.send_message(
            chat_id=callback.message.chat.id,
            text=f"⚡ Генерація для флоу *{flow.name}*...",
            parse_mode="Markdown",
        )

        process = await asyncio.create_subprocess_exec(
            "python",
            "/app/bot/generator_worker.py",
            str(flow.id),
            str(callback.message.chat.id),
            str(status_msg.message_id),
            bot.token,
            stdout=sys.stdout,
            stderr=sys.stderr,
        )

        task = asyncio.create_task(
            show_generated_posts(
                process=process,
                flow_id=flow.id,
                chat_id=callback.message.chat.id,
                status_msg_id=status_msg.message_id,
                bot=bot,
                flow=flow,
            )
        )
        return task

    except Exception as e:
        logging.error(f"Помилка запуску генерації: {e!s}")
        await callback.message.answer(f"❌ Помилка: {e!s}", parse_mode="Markdown")


async def show_generated_posts(
    process: asyncio.subprocess.Process,
    flow_id: int,
    chat_id: int,
    status_msg_id: int,
    bot: Bot,
    flow,
):
    try:
        _, stderr = await process.communicate()

        if process.returncode != 0:
            error_msg = stderr.decode().strip() if stderr else "Невідома помилка"
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=status_msg_id,
                text=f"❌ Помилка генерації: {error_msg}",
            )
            return

        post_service = Container.post_service()
        posts = await post_service.get_all_posts_in_flow(
            flow_id, status=PostStatus.DRAFT
        )

        if not posts:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=status_msg_id,
                text="ℹ️ Не знайдено згенерованих постів",
            )
            return

        await bot.delete_message(chat_id, status_msg_id)

        from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Переглянути згенеровані пости",
                        callback_data=f"view_generated_{flow.id}",
                    )
                ]
            ]
        )

        await bot.send_message(
            chat_id=chat_id,
            text=f"✅ Генерація для флоу *{flow.name}* завершена успішно!\n",
            parse_mode="Markdown",
            reply_markup=keyboard,
        )

    except Exception as e:
        logging.error(f"Помилка показу постів: {e!s}", exc_info=True)
        await bot.send_message(
            chat_id=chat_id, text=f"❌ Не вдалося показати пости: {e!s}"
        )
