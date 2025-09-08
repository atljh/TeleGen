import logging
from typing import cast

from aiogram import F, Router
from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager, StartMode

from bot.containers import Container
from bot.database.models import ChannelDTO, FlowDTO
from bot.dialogs.generation.flow.states import FlowMenu
from bot.services.channel_service import ChannelService
from bot.services.flow_service import FlowService

logger = logging.getLogger(__name__)

generation_router = Router()


@generation_router.callback_query(F.data.startswith("view_generated_"))
async def view_generated_posts(
    callback: CallbackQuery, dialog_manager: DialogManager
) -> None:
    try:
        parts = callback.data.split("_")
        if len(parts) != 3:
            logger.warning(f"Invalid callback data format: {callback.data}")
            await callback.answer("Невірний формат запиту")
            return

        try:
            flow_id = int(parts[-1])
        except ValueError:
            logger.warning(f"Invalid flow ID in callback data: {callback.data}")
            await callback.answer("Невірний ідентифікатор флоу")
            return

        flow_service = cast(FlowService, Container.flow_service())
        channel_service = cast(ChannelService, Container.channel_service())

        flow = await flow_service.get_flow_by_id(flow_id)
        if not flow:
            logger.warning(f"Flow not found for ID: {flow_id}")
            await callback.answer("Флоу не знайдено")
            return
        channel = await channel_service.get_channel_by_db_id(flow.channel_id)
        if not channel:
            logger.warning(f"Channel not found for flow ID: {flow_id}")
            await callback.answer("Канал не знайдено")
            return

        await dialog_manager.start(
            FlowMenu.posts_list,
            data={
                "selected_channel": channel,
                "channel_flow": flow,
            },
            mode=StartMode.RESET_STACK,
        )

        await callback.answer()

    except Exception as e:
        logger.error(f"Error in view_generated_posts: {str(e)}", exc_info=True)
        await callback.answer("Сталася помилка при обробці запиту")
