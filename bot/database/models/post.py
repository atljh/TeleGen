from datetime import datetime
from enum import StrEnum
from typing import Any, Self

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
    video_url: str | None = None

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name = True
    )
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

        video_url = next(
            (
                media["path"]
                for media in raw_post.get("media", [])
                if media["type"] == "video"
            ),
            None,
        )

        status = PostStatus.DRAFT
        if raw_post.get("is_published", False):
            status = PostStatus.PUBLISHED
        elif raw_post.get("scheduled_time"):
            status = PostStatus.SCHEDULED

        return cls(
            content=raw_post.get("text", ""),
            source_url=raw_post.get("source", {}).get("link"),
            images=images,
            video_url=video_url,
            status=status,
            original_link=raw_post.get("original_link"),
            original_date=raw_post.get("original_date"),
            source_id=raw_post.get("source_id"),
            flow_id=0,
            created_at=datetime.now(),
        )

    @classmethod
    def from_orm(cls, obj: Any) -> Self:
        data = {}
        for field in cls.model_fields:
            value = getattr(obj, field, None)

            if field == "images":
                value = [
                    PostImageDTO(url=img.image.url, order=img.order)
                    for img in obj.images.all()
                ]

            elif field == "media_url":
                value = obj.first_image_url or (obj.video.url if obj.video else None)

            elif field == "video_url":
                value = obj.video.url if obj.video else None

            else:
                value = getattr(obj, field, None)

            data[field] = value

        return cls.model_validate(data, from_attributes=True)
