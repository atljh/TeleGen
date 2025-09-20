import logging
import os
import shutil
import tempfile
import uuid
from urllib.parse import urlparse

import aiofiles
import httpx
from django.conf import settings
from PIL import Image, UnidentifiedImageError

from admin_panel.admin_panel.models import Post, PostImage, PostVideo


class MediaService:
    def __init__(self):
        self.image_dir = "posts/images"
        self.video_dir = "posts/videos"
        self.logger = logging.getLogger(__name__)

    async def _download_remote_media(self, url: str, media_type: str) -> str:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36",
            "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Referer": "https://www.google.com/",
        }

        domain = urlparse(url).netloc
        if "atptour.com" in domain:
            headers["Referer"] = "https://www.atptour.com/"
        elif "sportarena.com" in domain:
            headers["Referer"] = "https://sportarena.com/"

        ext = os.path.splitext(urlparse(url).path)[1] or (
            ".jpg" if media_type == "image" else ".mp4"
        )
        temp_file = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}{ext}")

        try:
            async with httpx.AsyncClient(
                timeout=30, follow_redirects=True, headers=headers
            ) as client:
                resp = await client.get(url)
                resp.raise_for_status()

                async with aiofiles.open(temp_file, "wb") as f:
                    await f.write(resp.content)

            return temp_file
        except Exception:
            self.logger.error(f"Failed to download media from {url}")
            raise

    def _validate_image(self, file_path: str) -> None:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Image not found: {file_path}")
        try:
            with Image.open(file_path) as img:
                img.verify()
        except (OSError, UnidentifiedImageError) as e:
            raise ValueError(f"Invalid image: {file_path} - {e!s}") from e

    def _get_media_extension(self, file_path: str, media_type: str) -> str:
        return ".jpg" if media_type == "image" else ".mp4"

    def _get_permanent_media_path(self, media_type: str, extension: str) -> str:
        media_dir = self.image_dir if media_type == "image" else self.video_dir
        permanent_dir = os.path.join(settings.MEDIA_ROOT, media_dir)
        os.makedirs(permanent_dir, exist_ok=True)
        filename = f"{uuid.uuid4()}{extension}"
        return os.path.join(media_dir, filename)

    def _store_local_media(self, file_path: str, media_type: str) -> str:
        if media_type == "image":
            self._validate_image(file_path)
        extension = self._get_media_extension(file_path, media_type)
        permanent_path = self._get_permanent_media_path(media_type, extension)

        shutil.copy2(file_path, os.path.join(settings.MEDIA_ROOT, permanent_path))
        return permanent_path

    async def process_media_list(
        self, post: Post, media_list: list[dict] | None = None
    ) -> dict[str, list[str]]:
        """
        Saves media (images and videos) and links them to ORM post.
        Returns stored paths.
        media_list = [{"path": str, "type": "image"|"video", "order": int}]
        """
        stored_images: list[str] = []
        stored_videos: list[str] = []

        if not media_list:
            return {"images": stored_images, "videos": stored_videos}

        for media in media_list:
            try:
                path = media["path"]
                media_type = media["type"]

                if media_type == "image":
                    if path.startswith("/tmp/"):
                        stored_path = await self.store_media(path, media_type)
                        stored_images.append(stored_path)
                    else:
                        stored_images.append(media["path"])
                elif media_type == "video":
                    stored_path = await self.store_media(path, media_type)
                    stored_videos.append(stored_path)
                else:
                    self.logger.warning(f"Unknown media type: {media_type} for {path}")

            except Exception as e:
                self.logger.error(f"Failed to process media {media.get('path')}: {e!s}")
                continue

        for order, img_path in enumerate(stored_images):
            if img_path.startswith("posts/"):
                await PostImage.objects.acreate(post=post, image=img_path, order=order)
            else:
                await PostImage.objects.acreate(post=post, url=img_path, order=order)

        for order, vid_path in enumerate(stored_videos):
            await PostVideo.objects.acreate(post=post, video=vid_path, order=order)

        return {"images": stored_images, "videos": stored_videos}

    async def store_media(self, file_path_or_url: str, media_type: str) -> str:
        temp_file = None
        original_is_url = file_path_or_url.startswith(("http://", "https://"))

        try:
            if original_is_url:
                temp_file = await self._download_remote_media(
                    file_path_or_url, media_type
                )
                file_path = temp_file
            else:
                file_path = file_path_or_url

            stored_path = self._store_local_media(file_path, media_type)
            self.logger.info(f"Successfully stored media: {stored_path}")
            return stored_path

        except Exception as e:
            self.logger.error(f"Failed to store media {file_path_or_url}: {e!s}")
            raise
        finally:
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception as e:
                    self.logger.warning(
                        f"Failed to remove temp file {temp_file}: {e!s}"
                    )
