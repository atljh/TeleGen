from django.db import transaction
from asgiref.sync import sync_to_async
from bot.database.dtos.dtos import FlowDTO
from bot.database.dtos import AISettingsDTO
from bot.database.exceptions import AISettingsNotFoundError
from bot.database.repositories import AISettingsRepository, UserRepository

class AISettingsService:
    def __init__(
        self,
        repository: AISettingsRepository,
        user_repository: UserRepository,
    ):
        self.aisettings_repository = repository
        self.user_repository = user_repository

    async def create_aisettings(
        self,
        flow: FlowDTO,
        prompt: str,
        style: str
    ) -> AISettingsDTO:
        aisettings = await self.aisettings_repository.create_ai_settings(
            flow=flow,
            prompt=prompt,
            style=style
        )
        return AISettingsDTO.from_orm(aisettings)

    async def get_aisettings_by_flow(self, flow: FlowDTO) -> AISettingsDTO:
        aisettings = await self.aisettings_repository.get_ai_settings_by_flow(flow)
        return AISettingsDTO.from_orm(aisettings)
