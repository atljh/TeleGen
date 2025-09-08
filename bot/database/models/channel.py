from datetime import datetime
from pydantic import BaseModel, Field
from typing import Any, Self


class ChannelDTO(BaseModel):
    id: int
    user_id: int
    channel_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str | None = None
    created_at: datetime
    is_active: bool = True
    notifications: bool = True
    timezone: str = "UTC"

    class Config:
        from_attributes = True
        json_encoders = {datetime: lambda v: v.isoformat()}

    @classmethod
    def from_orm(cls, obj: Any) -> Self:
        return super().model_validate(obj)
