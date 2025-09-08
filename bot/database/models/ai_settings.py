from datetime import datetime
from typing import Any, Self
from pydantic import BaseModel, ConfigDict


class AISettingsDTO(BaseModel):
    id: int
    flow_id: int
    prompt: str
    style: str | None = None
    role: str | None = None
    role_content: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm(cls, obj: Any) -> Self:
        return cls.model_validate(obj)
