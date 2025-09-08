import logging
from urllib.parse import urlparse
from bs4 import BeautifulSoup


class ImageExtractorService:
    def __init__(
        self,
        logger: logging.Logger | None = None
    ):
        self.decorative_classes = {'icon', 'logo', 'button'}
        self.min_size = (400, 250)
        self.logger = logger or logging.getLogger(__name__)

    def extract_images(self, soup: BeautifulSoup, base_url: str) -> list[str]:
        images = []
        for img in soup.find_all('img'):
            img_url = self._normalize_url(img.get('src'), base_url)
            if img_url and self._is_valid_image(img, img_url):
                images.append(img_url)
        return list(dict.fromkeys(images))[:5]

    def _is_valid_image(self, img_tag, img_url: str) -> bool:
        if img_url.endswith('.svg'):
            return False

        width = self._get_dimension(img_tag, 'width')
        height = self._get_dimension(img_tag, 'height')

        return (width >= self.min_size[0] and
                height >= self.min_size[1] and
                not self._is_decorative(img_tag))

    def _is_decorative(self, img_tag) -> bool:
        classes = img_tag.get('class', [])
        if isinstance(classes, str):
            classes = classes.split()
        return any(cls in self.decorative_classes for cls in classes)

    def _get_dimension(self, tag, attr: str) -> int:
        value = tag.get(attr, 0)
        return int(value) if str(value).isdigit() else 0

    def _normalize_url(self, url: str, base_url: str) -> str | None:
        if not url or url.startswith('data:'):
            return None
        parsed = urlparse(url)
        if not parsed.netloc:
            base = urlparse(base_url)
            return f"{base.scheme}://{base.netloc}{url}"
        return url