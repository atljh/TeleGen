import asyncio
import logging
import os
import shutil
import tempfile
import uuid
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse

import httpx
from asgiref.sync import sync_to_async
from django.conf import settings
from django.db import IntegrityError
from django.db.models import Prefetch
from psycopg.errors import UniqueViolation
from PIL import Image, UnidentifiedImageError

from admin_panel.admin_panel.models import Flow, Post, PostImage
from bot.database.exceptions import PostNotFoundError
from bot.database.models import MediaType, PostDTO, PostStatus


class PostRepository:
    async def create(
        self,
        flow: Flow,
        content: str,
        source_url: Optional[str] = None,
        status: PostStatus = None,
        scheduled_time: Optional[datetime] = None,
        images: Optional[list[str]] = None,
        video_path: Optional[str] = None,
    ) -> Post:
        post = Post(
            flow=flow,
            content=content,
            source_url=source_url,
            status=status,
            scheduled_time=scheduled_time,
        )
        await post.asave()

        if video_path:
            await self._save_video_from_path(post, video_path)

        if images:
            for image_path in images:
                await self._save_image_from_path(post, image_path)

        return post

    async def create_with_media(
        self,
        flow: Flow,
        content: str,
        media_list: list[dict],
        original_link: str,
        original_date: datetime,
        source_url: str,
        source_id: str,
        original_content: str,
        scheduled_time: Optional[datetime] = None,
    ) -> Optional[Post]:
        try:
            if await self._post_exists(source_id):
                return None

            return await self._create_post_with_media_transaction(
                flow=flow,
                content=content,
                media_list=media_list,
                original_link=original_link,
                original_date=original_date,
                original_content=original_content,
                source_url=source_url,
                source_id=source_id,
                scheduled_time=scheduled_time,
            )

        except IntegrityError as e:
            return await self._handle_integrity_error(e, source_id)
        except Exception as e:
            logging.error(f"Unexpected error: {str(e)}")
            raise

    async def _post_exists(self, source_id: str) -> bool:
        exists = await Post.objects.filter(source_id=source_id).aexists()
        if exists:
            logging.warning(f"Duplicate post skipped: {source_id}")
        return exists

    async def _create_post_with_media_transaction(
        self,
        flow: Flow,
        content: str,
        media_list: list[dict],
        original_link: str,
        original_date: datetime,
        source_url: str,
        source_id: str,
        original_content: str,
        scheduled_time: Optional[datetime] = None,
    ) -> Post:
        @sync_to_async
        def _create_post_sync():
            return self._create_post(
                flow=flow,
                content=content,
                original_content=original_content,
                original_link=original_link,
                original_date=original_date,
                source_url=source_url,
                source_id=source_id,
                scheduled_time=scheduled_time,
            )

        post = await _create_post_sync()
        await self._process_media_list(post, media_list)
        return post

    def _create_post(
        self,
        flow: Flow,
        content: str,
        original_link: str,
        original_date: datetime,
        source_url: str,
        source_id: str,
        original_content: str,
        scheduled_time: Optional[datetime] = None,
    ) -> Post:
        return Post.objects.create(
            flow=flow,
            content=content,
            original_content=original_content,
            original_link=original_link,
            original_date=original_date,
            source_url=source_url,
            source_id=source_id,
            status=PostStatus.DRAFT,
            scheduled_time=scheduled_time,
        )

    async def _process_media_list(self, post: Post, media_list: list[dict]):
        for media in media_list:
            try:
                await self._process_single_media(post, media)
            except Exception as e:
                logging.error(f"Failed to process media: {str(e)}")
                continue

    async def _process_single_media(self, post: Post, media: dict):
        media_type = media.get("type")
        local_path = media.get("path")

        if not local_path or not media_type:
            return

        permanent_path = await self._store_media_permanently(
            local_path, "images" if media_type == MediaType.IMAGE.value else "videos"
        )

        if media_type == MediaType.IMAGE.value:
            await sync_to_async(self._create_post_image)(post, permanent_path)
        elif media_type == MediaType.VIDEO.value:
            await sync_to_async(self._update_post_video)(post, permanent_path)

    def _create_post_image(self, post: Post, image_path: str):
        PostImage.objects.create(post=post, image=image_path, order=post.images.count())

    def _update_post_video(self, post: Post, video_path: str):
        post.video = video_path
        post.save()

    async def _handle_integrity_error(
        self, error: IntegrityError, source_id: str
    ) -> Optional[Post]:
        if isinstance(error.__cause__, UniqueViolation):
            logging.warning(f"Duplicate post detected (source_id: {source_id})")
            return await Post.objects.filter(source_id=source_id).afirst()
        logging.error(f"Database error: {str(error)}")
        raise error

    async def _download_remote_media(self, url: str, media_type: str) -> str:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
            "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "image",
            "Sec-Fetch-Mode": "no-cors",
            "Sec-Fetch-Site": "cross-site",
            "Referer": "https://www.google.com/",
        }

        domain = urlparse(url).netloc
        if "atptour.com" in domain:
            headers["Referer"] = "https://www.atptour.com/"
        elif "sportarena.com" in domain:
            headers["Referer"] = "https://sportarena.com/"

        ext = os.path.splitext(urlparse(url).path)[1] or (
            ".jpg" if media_type == "images" else ".mp4"
        )
        temp_file = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}{ext}")

        try:
            async with httpx.AsyncClient(
                timeout=30,
                follow_redirects=True,
                headers=headers
            ) as client:
                resp = await client.get(url)
                resp.raise_for_status()

                with open(temp_file, "wb") as f:
                    f.write(resp.content)

            return temp_file

        except httpx.HTTPStatusError as e:
            logging.warning(f"HTTP error {e.response.status_code} for URL: {url}")
            raise
        except Exception as e:
            logging.error(f"Failed to download media from {url}: {str(e)}")
            raise


    def _validate_image(self, file_path: str) -> None:
        try:
            with Image.open(file_path) as img:
                img.verify()
        except (UnidentifiedImageError, IOError) as e:
            raise ValueError(f"Invalid image file: {file_path} - {str(e)}")


    def _get_media_extension(self, file_path: str, media_type: str) -> str:
        ext = os.path.splitext(file_path)[1].lower()
        if ext:
            return ext

        return ".jpg" if media_type == "images" else ".mp4"


    def _get_permanent_media_path(self, media_type: str, extension: str) -> str:
        media_dir = "posts/images" if media_type == "images" else "posts/videos"
        permanent_dir = os.path.join(settings.MEDIA_ROOT, media_dir)
        os.makedirs(permanent_dir, exist_ok=True)

        filename = f"{uuid.uuid4()}{extension}"
        return os.path.join(media_dir, filename)


    async def _store_media_permanently(
        self, file_path_or_url: str, media_type: str
    ) -> str:

        temp_file = None
        original_is_url = file_path_or_url.startswith(("http://", "https://"))

        try:
            if original_is_url:
                temp_file = await self._download_remote_media(file_path_or_url, media_type)
                file_path = temp_file
            else:
                file_path = file_path_or_url

            if media_type == "images":
                self._validate_image(file_path)

            extension = self._get_media_extension(file_path, media_type)
            permanent_path = self._get_permanent_media_path(media_type, extension)

            shutil.copy2(file_path, os.path.join(settings.MEDIA_ROOT, permanent_path))

            logging.info(f"Successfully stored media: {permanent_path}")
            return permanent_path

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 403:
                logging.warning(f"Access denied (403) for URL: {file_path_or_url}")
                return await self._try_alternative_download(file_path_or_url, media_type)
            raise

        except Exception as e:
            logging.error(f"Failed to store media {file_path_or_url}: {str(e)}")
            raise

        finally:
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception as e:
                    logging.warning(f"Failed to remove temp file {temp_file}: {str(e)}")


    async def _try_alternative_download(self, url: str, media_type: str) -> str:
        try:
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/91.0.4472.124 Safari/537.36"
                ),
                "Accept": "*/*",
                "Referer": "https://www.google.com/",
            }

            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(url, headers=headers)
                resp.raise_for_status()

                ext = os.path.splitext(urlparse(url).path)[1] or ".jpg"
                temp_file = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}{ext}")

                with open(temp_file, "wb") as f:
                    f.write(resp.content)

                return await self._store_local_media(temp_file, media_type, is_temp=True)

        except Exception as e:
            logging.warning(f"Alternative download failed for {url}: {str(e)}")
            raise


    async def _store_local_media(self, file_path: str, media_type: str, is_temp: bool = False) -> str:
        try:
            if media_type == "images":
                self._validate_image(file_path)

            extension = self._get_media_extension(file_path, media_type)
            permanent_path = self._get_permanent_media_path(media_type, extension)

            shutil.copy2(file_path, os.path.join(settings.MEDIA_ROOT, permanent_path))
            return permanent_path

        finally:
            if is_temp and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception:
                    pass

    async def get(self, post_id: int) -> Post:
        try:
            query = Post.objects.select_related("flow").prefetch_related("images")
            return await query.aget(id=post_id)
        except Post.DoesNotExist:
            raise PostNotFoundError(f"Post with id={post_id} not found")

    async def update_media(
        self, post_id: int, media_file, filename: str, media_type: MediaType
    ) -> Post:
        post = await self.get(post_id)

        if post.image:
            post.image.delete(save=False)
        if post.video:
            post.video.delete(save=False)

        if media_type == MediaType.IMAGE:
            post.image.save(filename, media_file, save=False)
        elif media_type == MediaType.VIDEO:
            post.video.save(filename, media_file, save=False)

        await post.asave()
        return post

    async def remove_media(self, post_id: int) -> Post:
        post = await self.get(post_id)
        if post.image:
            post.image.delete(save=False)
            post.image = None
        if post.video:
            post.video.delete(save=False)
            post.video = None
        await post.asave()
        return post

    async def get_posts_by_flow_id(
        self, flow_id: int, status: PostStatus = None
    ) -> list[PostDTO]:
        posts = await self._fetch_posts_from_db(flow_id, status=status)
        # await self._preload_media_for_posts(posts)
        return posts

    @sync_to_async
    def _fetch_posts_from_db(
        self, flow_id: int, status: PostStatus = None
    ) -> list[PostDTO]:
        posts = Post.objects.filter(flow_id=flow_id)

        if status is not None:
            posts = posts.filter(status=status)
        else:
            posts = posts.filter(status__in=[PostStatus.PUBLISHED, PostStatus.DRAFT])

        posts = (
            posts.select_related("flow")
            .prefetch_related(
                Prefetch(
                    "images",
                    queryset=PostImage.objects.only("image", "order").order_by("order"),
                )
            )
            .only(
                "id",
                "content",
                "source_url",
                "publication_date",
                "status",
                "created_at",
                "scheduled_time",
                "video",
                "flow__id",
                "flow__name",
                "original_link",
                "original_date",
                "source_url",
            )
            .order_by("-created_at")
        )

        return [PostDTO.from_orm(post) for post in posts]

    async def _preload_media_for_posts(self, posts: list[PostDTO]):
        tasks = []

        for post in posts[:3]:
            if post.images:
                tasks.append(self._preload_media(post.images[0].url, "image"))
            elif post.video_url:
                tasks.append(self._preload_media(post.video_url, "video"))

        if tasks:
            await asyncio.gather(*tasks)

    async def _preload_media(self, media_url: str, media_type: str) -> bool:
        try:
            if not media_url:
                return False

            media_path = os.path.join(
                settings.MEDIA_ROOT,
                media_url.replace(settings.MEDIA_URL, "").lstrip("/"),
            )

            if os.path.exists(media_path):
                return True
            return False

        except Exception as e:
            logging.error(f"Error preloading media {media_url}: {str(e)}")
            return False

    async def exists(self, post_id: int) -> bool:
        return await Post.objects.filter(id=post_id).aexists()

    async def list(
        self,
        flow_id: Optional[int] = None,
        status: Optional[str] = None,
        is_published: Optional[bool] = None,
        scheduled_before: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Post]:
        query = Post.objects.all()

        if flow_id:
            query = query.filter(flow_id=flow_id)
        if status:
            query = query.filter(status=status)
        if is_published is not None:
            query = query.filter(is_published=is_published)
        if scheduled_before:
            query = query.filter(scheduled_time__lte=scheduled_before)

        return [
            post
            async for post in query.select_related("flow").order_by("-created_at")[
                offset : offset + limit
            ]
        ]

    async def count_posts_in_flow(self, flow_id: int) -> int:
        return await Post.objects.filter(flow_id=flow_id).acount()

    async def update(self, post_id: int, **fields) -> Post:
        post = await self.get(post_id)
        for field, value in fields.items():
            setattr(post, field, value)
        await post.asave()
        return post

    async def delete(self, post_id: int) -> None:
        post = await self.get(post_id)
        await post.adelete()

    async def schedule_post(self, post_id: int, scheduled_time: datetime) -> None:
        await sync_to_async(Post.objects.filter(id=post_id).update)(
            scheduled_time=scheduled_time, status=PostStatus.SCHEDULED
        )
