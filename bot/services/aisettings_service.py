from bot.database.dtos import AISettingsDTO
from bot.database.repositories import AISettingsRepository, UserRepository
from bot.database.exceptions import AISettingsNotFoundError, UserNotFoundError

class AISettingsService:
    def __init__(
        self,
        aisettings_repository: AISettingsRepository,
        user_repository: UserRepository
    ):
        self.aisettings_repository = aisettings_repository
        self.user_repository = user_repository

    async def create_aisettings(
        self,
        user_id: int,
        prompt: str,
        style: str
    ) -> AISettingsDTO:
        try:
            user = await self.user_repository.get_user_by_id(user_id)
        except UserNotFoundError:
            raise UserNotFoundError(f"Пользователь с id={user_id} не найден.")

        aisettings = await self.aisettings_repository.create_ai_settings(
            user=user,
            prompt=prompt,
            style=style
        )
        return AISettingsDTO.from_orm(aisettings)

    async def get_aisettings_by_user_id(self, user_id: int) -> AISettingsDTO:
        try:
            user = await self.user_repository.get_user_by_id(user_id)
        except UserNotFoundError:
            raise UserNotFoundError(f"Пользователь с id={user_id} не найден.")

        try:
            aisettings = await self.aisettings_repository.get_ai_settings_by_user(user)
            return AISettingsDTO.from_orm(aisettings)
        except AISettingsNotFoundError:
            raise AISettingsNotFoundError(f"Настройки ИИ для пользователя с id={user_id} не найдены.")