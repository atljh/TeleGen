from datetime import datetime
from enum import Enum
from typing import Any, ClassVar, TypedDict

from telethon.tl.types import Channel, Chat, User

TelegramEntity = Channel | Chat | User


class MediaType(str, Enum):
    IMAGE = "image"
    VIDEO = "video"
    DOCUMENT = "document"
    AUDIO = "audio"


class MediaInfo(TypedDict):
    type: MediaType
    media_obj: Any
    file_id: int | None
    path: str | None
    order: int | None


class SourceType(str, Enum):
    TELEGRAM = "telegram"
    WEB = "web"
    RSS = "rss"


class SourceInfo(TypedDict):
    type: SourceType
    link: str
    name: str | None
    priority: int | None


class RawPostData(TypedDict):
    original_content: str
    text: str
    media: list[MediaInfo]
    is_album: bool
    album_size: int
    original_link: str | None
    original_date: datetime | None
    source_url: str
    source_id: str | None


class ProcessedPostData(TypedDict):
    content: str
    original_content: str
    media: list[MediaInfo]
    original_link: str | None
    original_date: datetime | None
    source_url: str
    source_id: str | None
    flow_id: int | None
    status: str | None


class AlbumProcessingResult(TypedDict):
    post_data: RawPostData | None
    album_size: int


class MessageProcessingResult(TypedDict):
    post_data: RawPostData | None
    post_count: int


class UserbotConfig(TypedDict):
    api_id: int
    api_hash: str
    phone: str | None
    session_path: str | None
    download_concurrency: int
    max_retries: int
    timeout: float


class DownloadConfig(TypedDict):
    semaphore_limit: int
    max_file_size: int
    allowed_mime_types: list[str]
    temp_dir: str


class ProcessingConfig(TypedDict):
    max_text_length: int
    allowed_entities: list[str]
    external_links_check: bool
    duplicate_check: bool


class OperationResult(TypedDict):
    success: bool
    data: Any | None
    error: str | None
    execution_time: float


class BatchOperationResult(TypedDict):
    total: int
    successful: int
    failed: int
    results: list[OperationResult]


class UserbotStats(TypedDict):
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_downloads: int
    total_bytes_downloaded: int
    avg_processing_time: float
    last_activity: datetime


class SourceStats(TypedDict):
    source_url: str
    posts_processed: int
    posts_skipped: int
    avg_post_age: float
    success_rate: float


class UserbotError(Exception):
    pass


class AuthorizationError(UserbotError):
    pass


class ConnectionError(UserbotError):
    pass


class DownloadError(UserbotError):
    pass


class ProcessingError(UserbotError):
    pass


class RateLimitError(UserbotError):
    pass


class Constants:
    MAX_MESSAGE_LENGTH = 4096
    MAX_CAPTION_LENGTH = 1024
    MAX_MEDIA_GROUP_SIZE = 10
    DEFAULT_DOWNLOAD_LIMIT = 10
    MAX_RETRY_ATTEMPTS = 3
    RETRY_DELAY = 1.0
    SESSION_TIMEOUT = 30.0

    ALLOWED_MEDIA_TYPES: ClassVar[list[str]] = [
        "image/jpeg",
        "image/png",
        "image/gif",
        "video/mp4",
        "video/quicktime",
    ]

    EXTERNAL_LINK_DOMAINS: ClassVar[list[str]] = ["t.me", "telegram.me"]


def is_telegram_entity(entity: Any) -> bool:
    return isinstance(entity, Channel | Chat | User)


def is_valid_media_type(media_info: MediaInfo) -> bool:
    return media_info["type"] in [item.value for item in MediaType]


def is_valid_source_type(source_info: SourceInfo) -> bool:
    return source_info["type"] in [item.value for item in SourceType]


def validate_media_info(media_info: MediaInfo) -> bool:
    required_fields = ["type", "media_obj"]
    return all(field in media_info for field in required_fields)


def validate_source_info(source_info: SourceInfo) -> bool:
    required_fields = ["type", "link"]
    return all(field in source_info for field in required_fields)


def validate_raw_post_data(post_data: RawPostData) -> bool:
    required_fields = ["original_content", "text", "media", "is_album", "source_url"]
    return all(field in post_data for field in required_fields)
