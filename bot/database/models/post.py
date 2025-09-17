from datetime import datetime
from enum import StrEnum
from typing import Any

from asgiref.sync import sync_to_async
from pydantic import BaseModel, ConfigDict, Field, field_serializer


class MediaType(StrEnum):
    IMAGE = "image"
    VIDEO = "video"


class PostStatus(StrEnum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"


class PostImageDTO(BaseModel):
    url: str
    order: int = Field(default=0, ge=0)


class PostVideoDTO(BaseModel):
    url: str
    order: int = Field(default=0, ge=0)


class PostDTO(BaseModel):
    id: int | None = None
    flow_id: int
    content: str
    original_content: str | None = None
    source_id: str
    source_url: str | None = None
    publication_date: datetime | None = None
    status: PostStatus = PostStatus.DRAFT
    original_link: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)
    original_date: datetime | None = None
    scheduled_time: datetime | None = None
    media_type: MediaType | None = None
    media_url: str | None = None
    images: list[PostImageDTO] = Field(default_factory=list, alias="images_list")
    videos: list[PostVideoDTO] = Field(default_factory=list, alias="videos_list")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    @property
    def is_album(self) -> bool:
        return len(self.images) > 1

    @field_serializer("created_at")
    def serialize_created_at(self, v: datetime):
        return v.isoformat()

    @classmethod
    def from_raw_post(cls, raw_post: dict) -> "PostDTO":
        images = [
            PostImageDTO(url=media["path"], order=i)
            for i, media in enumerate(raw_post.get("media", []))
            if media["type"] == "image"
        ]

        videos = [
            PostVideoDTO(url=media["path"], order=i)
            for i, media in enumerate(raw_post.get("media", []))
            if media["type"] == "video"
        ]

        status = PostStatus.DRAFT
        if raw_post.get("is_published", False):
            status = PostStatus.PUBLISHED
        elif raw_post.get("scheduled_time"):
            status = PostStatus.SCHEDULED

        return cls(
            content=raw_post.get("text", ""),
            source_url=raw_post.get("source", {}).get("link"),
            images=images,
            videos=videos,
            status=status,
            original_link=raw_post.get("original_link"),
            original_date=raw_post.get("original_date"),
            source_id=raw_post.get("source_id"),
            flow_id=0,
            created_at=datetime.now(),
        )

    @classmethod
    async def from_orm_async(cls, obj: Any) -> "PostDTO":
        data = {}

        for field in cls.model_fields:
            if field == "images":
                images = await sync_to_async(list)(obj.images.all().order_by("order"))
                value = [
                    PostImageDTO(
                        url=str(img.image) if img.image else img.url, order=img.order
                    )
                    for img in images
                ]
            elif field == "videos":
                videos = await sync_to_async(list)(obj.videos.all().order_by("order"))
                value = [
                    PostVideoDTO(url=str(video.video), order=video.order)
                    for video in videos
                ]
            elif field == "media_type":
                images_exist = await sync_to_async(obj.images.exists)()
                videos_exist = await sync_to_async(obj.videos.exists)()
                if images_exist and not videos_exist:
                    value = MediaType.IMAGE
                elif videos_exist and not images_exist:
                    value = MediaType.VIDEO
                elif images_exist and videos_exist:
                    value = MediaType.VIDEO
                else:
                    value = None
            else:
                value = getattr(obj, field, None)

            data[field] = value

        return cls.model_validate(data, from_attributes=True)
