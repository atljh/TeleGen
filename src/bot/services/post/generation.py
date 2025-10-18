import asyncio
import logging

from aiogram import Bot
from asgiref.sync import sync_to_async

from admin_panel.models import Post
from bot.database.exceptions import GenerationLimitExceeded
from bot.database.models import PostDTO
from bot.database.repositories import FlowRepository
from bot.services.limit_service import LimitService
from bot.services.logger_service import SyncTelegramLogger, get_logger, init_logger
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
        self,
        flow_id: int,
        allow_partial: bool = False,
        auto_generate: bool = False,
    ) -> list[PostDTO]:
        flow = await self.flow_repo.get_flow_by_id(flow_id)
        if not flow:
            return []

        user = await sync_to_async(lambda: flow.channel.user)()

        try:
            await self.limit_service.check_generations_limit(user, new_generations=0)
        except GenerationLimitExceeded as e:
            raise e

        volumes = self._calculate_volumes(flow)
        web_volume = sum([v["volume"] for v in volumes if v["type"] == "web"])
        telegram_volume = sum([v["volume"] for v in volumes if v["type"] == "telegram"])

        if not self.logger:
            init_logger(self.bot)
            self.logger = get_logger()

        self.sync_logger.user_started_generation(
            user,
            flow_name=flow.name,
            flow_id=flow.id,
            web_volume=web_volume,
            telegram_volume=telegram_volume,
            auto_generate=auto_generate,
        )
        tasks = []
        for item in volumes:
            if item["volume"] <= 0:
                continue
            if item["type"] == "telegram":
                tasks.append(
                    self.userbot_service.get_last_posts(flow, item, item["volume"])
                )
            elif item["type"] == "web":
                tasks.append(
                    self.web_service.get_last_posts(flow, item, item["volume"])
                )

        results = await asyncio.gather(*tasks, return_exceptions=True)

        combined_posts: list[PostDTO] = []
        for r in results:
            if isinstance(r, Exception):
                self.logger.error(f"Error in source task: {r!s}")
            else:
                combined_posts.extend(r)

        combined_posts.sort(key=lambda x: x.created_at, reverse=True)

        try:
            await self.limit_service.check_generations_limit(
                user, new_generations=len(combined_posts)
            )
        except GenerationLimitExceeded as e:
            if not allow_partial:
                raise e
            tariff = await self.limit_service.get_user_tariff(user)
            remaining = tariff.generations_available - user.generated_posts_count
            combined_posts = combined_posts[:remaining]

        self.sync_logger.generation_completed(
            user=user,
            flow_name=flow.name,
            flow_id=flow.id,
            result=f"{len(combined_posts)} posts generated from {len(results)} sources",
            auto_generate=auto_generate,
        )

        user.generated_posts_count += len(combined_posts)
        await sync_to_async(user.save)()

        return await self._create_posts_from_dtos(flow, combined_posts)

    def _calculate_volumes(self, flow) -> list[dict]:
        total_volume = flow.flow_volume
        sources = flow.sources

        total_sources = len(sources)
        if total_sources == 0:
            return []

        base_volume = total_volume // total_sources
        remainder = total_volume % total_sources

        results = []
        for i, source in enumerate(sources):
            volume = base_volume + (1 if i < remainder else 0)
            results.append({**source, "volume": volume})

        return results

    async def _create_posts_from_dtos(
        self, flow, post_dtos: list[PostDTO]
    ) -> list[PostDTO]:
        semaphore = asyncio.Semaphore(10)

        existing_posts = await sync_to_async(
            lambda: list(Post.objects.filter(flow=flow).order_by("-created_at"))
        )()

        max_volume = flow.flow_volume or 30
        total_after_generation = len(existing_posts) + len(post_dtos)

        if total_after_generation > max_volume:
            to_remove = total_after_generation - max_volume
            oldest_posts = existing_posts[-to_remove:]
            if oldest_posts:
                ids_to_delete = [p.id for p in oldest_posts]
                await sync_to_async(Post.objects.filter(id__in=ids_to_delete).adelete)()
                msg = f"🧹 Flow '{flow.name}' (id={flow.id}): удалено {len(ids_to_delete)} старых постов"
                logging.info(msg)
                try:
                    self.sync_logger.log_message(msg)
                except Exception:
                    pass

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

        created_posts = [res for res in results if isinstance(res, PostDTO)]

        msg = (
            f"✅ Flow '{flow.name}' (id={flow.id}): создано {len(created_posts)} постов, "
            f"текущий размер ленты ≤ {max_volume}"
        )
        logging.info(msg)
        try:
            self.sync_logger.log_message(msg)
        except Exception:
            pass

        return created_posts

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
