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

from admin_panel.models import Post, PostImage, PostVideo


class MediaService:
    def __init__(self):
        self.image_dir = "posts/images"
        self.video_dir = "posts/videos"
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def _is_url(path: str) -> bool:
        """Check if path is a URL"""
        return path.startswith(("http://", "https://"))

    @staticmethod
    def _is_local_media_path(path: str) -> bool:
        """Check if path is a stored local media file"""
        return path.startswith("posts/") and not MediaService._is_url(path)

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

    async def validate_media_list(self, media_list: list[dict]) -> None:
        """
        Validate all media in the list before processing.
        Raises exception if any media is invalid.
        """
        if not media_list:
            return

        for media in media_list:
            path = media.get("path")
            media_type = media.get("type")

            if not path:
                raise ValueError("Media path is required")

            if media_type not in ("image", "video"):
                raise ValueError(f"Invalid media type: {media_type}")

            # For local temp files, validate they exist
            if path.startswith("/tmp/") and not os.path.exists(path):
                raise FileNotFoundError(f"Temp file not found: {path}")

            # For images in temp, validate format
            if media_type == "image" and path.startswith("/tmp/"):
                try:
                    self._validate_image(path)
                except Exception as e:
                    raise ValueError(f"Invalid image file {path}: {e!s}") from e

    async def process_media_list(
        self, post: Post, media_list: list[dict] | None = None
    ) -> dict[str, list[str]]:
        """
        Saves media (images and videos) and links them to ORM post.
        Returns stored paths.
        media_list = [{"path": str, "type": "image"|"video", "order": int}]

        IMPORTANT: This should be called within a transaction.
        If any media fails, the whole operation should rollback.
        """
        stored_images: list[str] = []
        stored_videos: list[str] = []

        if not media_list:
            return {"images": stored_images, "videos": stored_videos}

        # Process all media first, fail fast if any error
        for media in media_list:
            path = media["path"]
            media_type = media["type"]

            if media_type == "image":
                # Store temp files, keep URLs as-is
                if path.startswith("/tmp/"):
                    stored_path = await self.store_media(path, media_type)
                    stored_images.append(stored_path)
                elif self._is_url(path):
                    # Store remote URL images
                    stored_images.append(path)
                elif self._is_local_media_path(path):
                    # Already stored local file
                    stored_images.append(path)
                else:
                    self.logger.warning(f"Unknown image path format: {path}")
                    stored_images.append(path)

            elif media_type == "video":
                # Always store videos locally
                if not self._is_local_media_path(path):
                    stored_path = await self.store_media(path, media_type)
                    stored_videos.append(stored_path)
                else:
                    stored_videos.append(path)

        # Create database records
        for order, img_path in enumerate(stored_images):
            if self._is_local_media_path(img_path):
                await PostImage.objects.acreate(post=post, image=img_path, order=order)
            else:
                # It's a URL
                await PostImage.objects.acreate(post=post, url=img_path, order=order)

        for order, vid_path in enumerate(stored_videos):
            await PostVideo.objects.acreate(post=post, video=vid_path, order=order)

        return {"images": stored_images, "videos": stored_videos}

    async def store_media(self, file_path_or_url: str, media_type: str) -> str:
        """
        Store media file (local or remote URL) to permanent storage.

        Args:
            file_path_or_url: Path to local file or URL
            media_type: "image" or "video"

        Returns:
            Relative path to stored file (e.g. "posts/images/uuid.jpg")

        Raises:
            Exception if download or storage fails
        """
        temp_file = None
        stored_path = None
        original_is_url = self._is_url(file_path_or_url)

        try:
            if original_is_url:
                self.logger.info(f"Downloading {media_type} from {file_path_or_url}")
                temp_file = await self._download_remote_media(
                    file_path_or_url, media_type
                )
                file_path = temp_file
            else:
                file_path = file_path_or_url

            # Validate file exists
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Media file not found: {file_path}")

            stored_path = self._store_local_media(file_path, media_type)
            self.logger.info(f"Stored {media_type} to {stored_path}")
            return stored_path

        except httpx.HTTPStatusError as e:
            self.logger.error(
                f"HTTP error downloading {file_path_or_url}: {e.response.status_code}"
            )
            raise ValueError(
                f"Failed to download media: HTTP {e.response.status_code}"
            ) from e

        except httpx.TimeoutException as e:
            self.logger.error(f"Timeout downloading {file_path_or_url}")
            raise ValueError(
                f"Timeout downloading media from {file_path_or_url}"
            ) from e

        except Exception as e:
            self.logger.error(
                f"Failed to store media {file_path_or_url}: {e!s}", exc_info=True
            )
            # If we partially stored the file, try to clean it up
            if stored_path:
                try:
                    full_path = os.path.join(settings.MEDIA_ROOT, stored_path)
                    if os.path.exists(full_path):
                        os.remove(full_path)
                        self.logger.info(f"Cleaned up partial file: {stored_path}")
                except Exception as cleanup_err:
                    self.logger.warning(
                        f"Failed to cleanup partial file: {cleanup_err!s}"
                    )
            raise

        finally:
            # Always clean up temp files
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                    self.logger.debug(f"Removed temp file: {temp_file}")
                except Exception as e:
                    self.logger.warning(
                        f"Failed to remove temp file {temp_file}: {e!s}"
                    )
