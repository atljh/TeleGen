from datetime import datetime
from typing import Any, Self

from pydantic import BaseModel, ConfigDict, Field


class StatisticsDTO(BaseModel):
    id: int
    user_id: int
    channel_id: int
    total_posts: int = 0
    total_views: int = 0
    total_likes: int = 0
    last_updated: datetime = Field(default_factory=datetime.now)

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm(cls, obj: Any) -> Self:
        return super().model_validate(obj)
