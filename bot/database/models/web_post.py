from dataclasses import dataclass
from datetime import datetime
from typing import Self
from urllib.parse import urlparse

@dataclass
class WebPost:
    """
    Data class representing scraped web page content.

    Attributes:
        title: Page title
        content: Main text content
        url: Original page URL
        date: Publication date (if available)
        source: Domain name
        images: List of image URLs
    """
    title: str
    content: str
    url: str
    date: datetime | None = None
    source: str | None = None
    images: list[str] | None = None

    def __post_init__(self) -> None:
        self.source = self.source or urlparse(self.url).netloc
        self.images = self.images or []

    @property
    def has_images(self) -> bool:
        return len(self.images) > 0

    def add_image(self, image_url: str) -> Self:
        if image_url and image_url not in self.images:
            self.images.append(image_url)
        return self

    def to_dict(self) -> dict[str, str | list[str] | None]:
        return {
            'title': self.title,
            'content': self.content,
            'url': self.url,
            'date': self.date.isoformat() if self.date else None,
            'source': self.source,
            'images': self.images
        }