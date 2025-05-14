from bot.database.dtos import AISettingsDTO
from bot.database.dtos.dtos import FlowDTO
from bot.database.repositories import AISettingsRepository, UserRepository
from bot.database.exceptions import AISettingsNotFoundError, UserNotFoundError
from bot.database.repositories.flow_repository import FlowRepository

class AISettingsService:
    def __init__(
        self,
        aisettings_repository: AISettingsRepository,
        user_repository: UserRepository,
    ):
        self.aisettings_repository = aisettings_repository
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
        try:
            aisettings = await self.aisettings_repository.get_ai_settings_by_flow(flow)
            return AISettingsDTO.from_orm(aisettings)
        except AISettingsNotFoundError:
            raise AISettingsNotFoundError(f"Настройки ИИ для flow с {flow} не найдены.")