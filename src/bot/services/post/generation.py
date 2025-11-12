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

        # Check subscription and limits BEFORE starting generation
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

        # Group posts by source to ensure even distribution
        posts_by_source: list[list[PostDTO]] = []
        source_names: list[str] = []

        for i, r in enumerate(results):
            source_type = volumes[i].get("type", "unknown")
            source_link = volumes[i].get("link", "unknown")
            source_names.append(f"{source_type}:{source_link}")

            if isinstance(r, Exception):
                self.logger.error(f"Error in source task: {r!s}")
                posts_by_source.append([])
            else:
                # Sort each source's posts by date
                source_posts = sorted(
                    r, key=lambda x: x.original_date or x.created_at, reverse=True
                )
                posts_by_source.append(source_posts)

        # Distribute posts evenly across sources using round-robin
        combined_posts: list[PostDTO] = []
        source_indices = [0] * len(posts_by_source)  # Track position in each source

        while len(combined_posts) < flow.flow_volume:
            added_any = False
            for source_idx, source_posts in enumerate(posts_by_source):
                if len(combined_posts) >= flow.flow_volume:
                    break
                idx = source_indices[source_idx]
                if idx < len(source_posts):
                    combined_posts.append(source_posts[idx])
                    source_indices[source_idx] += 1
                    added_any = True

            # If no posts were added in this round, we're out of posts
            if not added_any:
                break

        # Log distribution
        distribution_info = ", ".join(
            [f"{source_names[i]}: {count}" for i, count in enumerate(source_indices)]
        )
        logging.info(
            f"Post distribution across sources - {distribution_info} | "
            f"Total: {len(combined_posts)}/{flow.flow_volume}"
        )

        # Check if no posts were generated
        if len(combined_posts) == 0 and len(volumes) > 0:
            error_msg = (
                f"⚠️ <b>Не вдалося згенерувати пости</b>\n\n"
                f"Flow: <code>{flow.name}</code> (ID: {flow.id})\n"
                f"Джерел: {len(results)}\n\n"
                f"Можливі причини:\n"
                f"• Вичерпана квота OpenAI API\n"
                f"• Помилки обробки контенту\n\n"
            )
            self.logger.warning(error_msg)
            try:
                self.sync_logger.log_message(error_msg)
            except Exception:
                pass

            self.sync_logger.generation_completed(
                user=user,
                flow_name=flow.name,
                flow_id=flow.id,
                result="0 posts generated - all posts failed AI processing",
                auto_generate=auto_generate,
            )
            return []

        try:
            await self.limit_service.check_generations_limit(
                user, new_generations=len(combined_posts)
            )
        except GenerationLimitExceeded as e:
            if not allow_partial:
                raise e
            tariff = await self.limit_service.get_user_tariff(user)
            remaining = tariff.generations_available - user.generated_posts_count

            # If no posts can be created due to limit, always raise
            if remaining <= 0:
                raise e

            combined_posts = combined_posts[:remaining]
            logging.warning(
                f"Generation limit reached: trimmed to {remaining} posts "
                f"(user has {user.generated_posts_count}/{tariff.generations_available})"
            )

        self.sync_logger.generation_completed(
            user=user,
            flow_name=flow.name,
            flow_id=flow.id,
            result=f"{len(combined_posts)} posts generated from {len(results)} sources",
            auto_generate=auto_generate,
        )

        created_posts = await self._create_posts_from_dtos(flow, combined_posts)
        logging.info(f"generate_auto_posts: _create_posts_from_dtos returned {len(created_posts)} posts")
        user.generated_posts_count += len(created_posts)
        await sync_to_async(user.save)()
        logging.info(f"generate_auto_posts: Returning {len(created_posts)} posts")
        return created_posts

    def _calculate_volumes(self, flow) -> list[dict]:
        total_volume = flow.flow_volume
        sources = flow.sources

        total_sources = len(sources)
        if total_sources == 0:
            return []

        # Request more posts than needed to account for duplicates and errors
        # We'll fetch 2x the desired amount, then trim to exact count later
        buffer_multiplier = 2
        buffered_volume = total_volume * buffer_multiplier

        base_volume = buffered_volume // total_sources
        remainder = buffered_volume % total_sources

        results = []
        for i, source in enumerate(sources):
            volume = base_volume + (1 if i < remainder else 0)
            results.append({**source, "volume": volume})

        return results

    async def _create_posts_from_dtos(
        self, flow, post_dtos: list[PostDTO]
    ) -> list[PostDTO]:
        """
        Creates posts from DTOs with proper error handling.

        Note: Posts are never deleted - all posts are kept in DB as history/backup.
        Dialogs only display the latest flow_volume posts.
        New posts gradually replace old ones in the display as they are generated.
        """
        logging.info(f"_create_posts_from_dtos: Starting with {len(post_dtos)} post DTOs for flow {flow.id}")
        semaphore = asyncio.Semaphore(10)

        # Get latest post date once to avoid multiple DB queries
        latest_post = await sync_to_async(
            Post.objects.filter(flow=flow).order_by("-original_date").first
        )()
        latest_date = latest_post.original_date if latest_post and latest_post.original_date else None

        # Create new posts with proper error handling
        async def _process_single_post(post_dto: PostDTO) -> PostDTO | None:
            async with semaphore:
                try:
                    # Skip if no source_id
                    if not post_dto.source_id:
                        logging.warning("Post DTO has no source_id, skipping")
                        return None

                    # Skip if post is older than existing posts
                    if post_dto.original_date and latest_date:
                        if post_dto.original_date <= latest_date:
                            logging.info(
                                f"Skipping old post {post_dto.source_id} from {post_dto.original_date} "
                                f"(latest in DB: {latest_date})"
                            )
                            return None

                    media_list = self._prepare_media_list(post_dto)

                    # create_post now handles duplicate checking internally
                    logging.debug(f"Creating post with source_id={post_dto.source_id}")
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
                        logging.info(f"✅ Post created: id={post.id}, source_id={post_dto.source_id}")
                        return await PostDTO.from_orm_async(post)
                    else:
                        logging.warning(f"Post already exists: source_id={post_dto.source_id}")
                        return None

                except Exception as e:
                    logging.error(
                        f"Post creation failed for source_id={post_dto.source_id}: {e!s}",
                        exc_info=True,
                    )
                    return None

        tasks = [_process_single_post(dto) for dto in post_dtos]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        logging.info(f"_create_posts_from_dtos: gather completed, processing {len(results)} results")
        created_posts = [res for res in results if isinstance(res, PostDTO)]

        logging.info(f"_create_posts_from_dtos: Created {len(created_posts)} posts out of {len(post_dtos)} DTOs")
        skipped_count = len(post_dtos) - len(created_posts)
        if skipped_count > 0:
            logging.info(
                f"Skipped {skipped_count} posts (duplicates or older than existing)"
            )

        # Count posts for statistics (no deletion, just reporting)
        draft_count = await sync_to_async(
            Post.objects.filter(flow=flow, status=Post.DRAFT).count
        )()
        published_count = await sync_to_async(
            Post.objects.filter(flow=flow, status=Post.PUBLISHED).count
        )()
        scheduled_count = await sync_to_async(
            Post.objects.filter(flow=flow, status=Post.SCHEDULED).count
        )()

        msg = (
            f"✅ Flow '{flow.name}' (id={flow.id}): створено {len(created_posts)} нових постів\n"
            f"📊 Статистика: чернеток={draft_count}, опубліковано={published_count}, заплановано={scheduled_count}\n"
            f"ℹ️ У діалозі показується останні {flow.flow_volume} чернеток"
        )
        logging.info(msg)
        try:
            self.sync_logger.log_message(msg)
        except Exception:
            pass

        logging.info(f"_create_posts_from_dtos: Returning {len(created_posts)} created posts")
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
