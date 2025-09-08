import re
from datetime import datetime
from enum import StrEnum
from typing import Any, Self

from pydantic import BaseModel, field_validator, validator


class ContentLength(StrEnum):
    TO_100 = "to_100"
    TO_300 = "to_300"
    TO_1000 = "to_1000"


class GenerationFrequency(StrEnum):
    HOURLY = "hourly"
    EVERY_12_HOURS = "12h"
    DAILY = "daily"


class FlowDTO(BaseModel):
    id: int
    channel_id: int
    name: str
    theme: str
    sources: list[dict[str, Any]]
    content_length: ContentLength = ContentLength.TO_300
    use_emojis: bool = True
    use_premium_emojis: bool = False
    title_highlight: bool = True
    cta: bool = False
    frequency: GenerationFrequency = GenerationFrequency.DAILY
    signature: str | None = None
    flow_volume: int = 5
    ad_time: str | None = None
    created_at: datetime
    updated_at: datetime | None = None
    next_generation_time: datetime | None = None
    last_generated_at: datetime | None = None

    @field_validator("ad_time")
    @classmethod
    def validate_ad_time(cls, v: str | None) -> str | None:
        if v and not re.match(r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$", v):
            raise ValueError("Invalid time format. Use HH:MM")
        return v

    class Config:
        from_attributes = True
        use_enum_values = True

    @classmethod
    def from_orm(cls, obj: Any) -> Self:
        return super().model_validate(obj)
