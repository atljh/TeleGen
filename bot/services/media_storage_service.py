import os
import shutil
from datetime import datetime
from django.conf import settings
from PIL import Image, UnidentifiedImageError


class MediaStorageService:
    def _validate_image(self, image_path: str) -> None:
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")
        try:
            with Image.open(image_path) as img:
                img.verify()
        except (IOError, UnidentifiedImageError) as e:
            raise ValueError(f"Invalid image: {image_path} - {str(e)}")

    def _copy_to_storage(self, source_path: str, subdir: str) -> str:
        target_dir = os.path.join(settings.MEDIA_ROOT, subdir)
        os.makedirs(target_dir, exist_ok=True)

        filename = f"{os.path.splitext(os.path.basename(source_path))[0]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{os.path.splitext(source_path)[1]}"
        destination = os.path.join(target_dir, filename)

        shutil.copy2(source_path, destination)
        return os.path.relpath(destination, settings.MEDIA_ROOT)

    def save_image(self, image_path: str) -> str:
        self._validate_image(image_path)
        return self._copy_to_storage(image_path, "images")

    def save_video(self, video_path: str) -> str:
        return self._copy_to_storage(video_path, "videos")
