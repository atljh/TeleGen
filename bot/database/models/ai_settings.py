from datetime import datetime
from pydantic import BaseModel
from typing import Any, Self


class AISettingsDTO(BaseModel):
    id: int
    flow_id: int
    prompt: str
    style: str | None = None
    role: str | None = None
    role_content: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, obj: Any) -> Self:
        return super().model_validate(obj)
