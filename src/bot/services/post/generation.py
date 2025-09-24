import asyncio
import logging

from aiogram import Bot
from asgiref.sync import sync_to_async

from admin_panel.models import Flow, Post
from bot.database.exceptions import GenerationLimitExceeded
from bot.database.models import PostDTO
from bot.database.repositories import FlowRepository
from bot.services.limit_service import LimitService
from bot.services.logger_service import SyncTelegramLogger, get_logger
from bot.services.post import PostBaseService
from bot.services.telegram_userbot import EnhancedUserbotService
from bot.services.web.web_service import WebService


class PostGenerationService:
    def __init__(
        self,
        userbot_service: EnhancedUserbotService,
        web_service: WebService,
        flow_repository: FlowRepository,
        post_base_service: PostBaseService,
        bot: Bot,
    ):
        self.userbot_service = userbot_service
        self.web_service = web_service
        self.flow_repo = flow_repository
        self.post_service = post_base_service
        self.bot = bot
        self.sync_logger = SyncTelegramLogger(bot.token)
        self.limit_service = LimitService()
        self.logger = get_logger()

    async def generate_auto_posts(
        self, flow_id: int, allow_partial: bool = False
    ) -> list[PostDTO]:
        flow = await self.flow_repo.get_flow_by_id(flow_id)
        if not flow:
            return []

        user = await sync_to_async(lambda: flow.channel.user)()
        tariff = await self.limit_service.get_user_tariff(user)
        if not tariff:
            return []

        remaining = tariff.generations_available - user.generated_posts_count
        if remaining <= 0:
            raise GenerationLimitExceeded(
                f"❌ Ліміт генерацій досягнуто ({tariff.generations_available}/місяць)"
            )

        requested = self._calculate_requested_volume(flow)
        max_to_generate = self._resolve_generation_volume(
            requested, remaining, allow_partial
        )

        combined_posts = await self._fetch_candidate_posts(flow)

        combined_posts = combined_posts[:max_to_generate]

        created = await self._create_posts_from_dtos(flow, combined_posts)
        await self.limit_service.increment_generations(user, len(created))

        return created

    def _calculate_volumes(self, flow) -> tuple[int, int]:
        total_volume = flow.flow_volume
        sources = flow.sources

        count_telegram = sum(1 for item in sources if item["type"] == "telegram")
        count_web = sum(1 for item in sources if item["type"] == "web")

        total_sources = count_telegram + count_web
        if total_sources == 0:
            return (0, 0)

        base_volume = total_volume // total_sources
        remainder = total_volume % total_sources

        telegram_userbot_volume = base_volume * count_telegram
        web_volume = base_volume * count_web

        if remainder:
            web_volume += remainder

        return (telegram_userbot_volume, web_volume)

    async def _create_posts_from_dtos(self, flow, post_dtos: list) -> list[PostDTO]:
        semaphore = asyncio.Semaphore(10)

        async def _process_single_post(post_dto: PostDTO) -> PostDTO | None:
            async with semaphore:
                try:
                    exists = await Post.objects.filter(
                        source_id=post_dto.source_id
                    ).aexists()
                    if exists:
                        logging.info(f"Skipping duplicate post: {post_dto.source_id}")
                        return None

                    media_list = self._prepare_media_list(post_dto)
                    post = await self.post_service.create_post(
                        flow=flow,
                        content=post_dto.content,
                        source_url=post_dto.source_url,
                        original_date=post_dto.original_date,
                        original_link=post_dto.original_link,
                        original_content=post_dto.original_content,
                        source_id=post_dto.source_id,
                        media_list=media_list,
                    )

                    if post:
                        return await PostDTO.from_orm_async(post)

                except Exception as e:
                    logging.error(f"Post creation failed: {e!s}", exc_info=True)
                    return None

        tasks = [_process_single_post(dto) for dto in post_dtos]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        return [res for res in results if isinstance(res, PostDTO)]

    def _prepare_media_list(self, post_dto) -> list[dict]:
        media_list = [
            {"path": img.url, "type": "image", "order": img.order}
            for img in post_dto.images
        ]

        for video in getattr(post_dto, "videos", []):
            media_list.append(
                {"path": video.url, "type": "video", "order": video.order}
            )

        return media_list

    def _calculate_requested_volume(self, flow: Flow) -> int:
        telegram_volume, web_volume = self._calculate_volumes(flow)
        return telegram_volume + web_volume

    def _resolve_generation_volume(
        self, requested: int, remaining: int, allow_partial: bool
    ) -> int:
        if requested > remaining and not allow_partial:
            raise GenerationLimitExceeded(
                f"❌ Недостатньо генерацій для {requested} постів "
                f"(доступно {remaining})"
            )
        return min(requested, remaining)

    async def _fetch_candidate_posts(self, flow: Flow) -> list[PostDTO]:
        telegram_volume, web_volume = self._calculate_volumes(flow)

        userbot_posts = await self.userbot_service.get_last_posts(flow, telegram_volume)
        web_posts = await self.web_service.get_last_posts(flow, web_volume)

        combined = userbot_posts + web_posts
        combined.sort(key=lambda x: x.created_at, reverse=True)
        return combined
