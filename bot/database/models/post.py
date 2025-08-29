from datetime import datetime
from enum import StrEnum
from pydantic import BaseModel, Field
from typing import Any, Self

class MediaType(StrEnum):
    IMAGE = "image"
    VIDEO = "video"

class PostStatus(StrEnum):
    DRAFT = 'draft'
    SCHEDULED = 'scheduled'
    PUBLISHED = 'published'

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

    @property
    def is_album(self) -> bool:
        return len(self.images) > 1
    
    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
        populate_by_name = True

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
