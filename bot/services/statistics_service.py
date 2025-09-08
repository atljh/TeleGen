import logging

from bot.database.models import StatisticsDTO
from bot.database.repositories import (
    ChannelRepository,
    StatisticsRepository,
    UserRepository,
)


class StatisticsService:
    def __init__(
        self,
        statistics_repository: StatisticsRepository,
        user_repository: UserRepository,
        channel_repository: ChannelRepository,
        logger: logging.Logger | None = None,
    ):
        self.statistics_repository = statistics_repository
        self.user_repository = user_repository
        self.channel_repository = channel_repository
        self.logger = logger or logging.getLogger(__name__)

    async def get_statistics_by_id(self, statistics_id: int) -> StatisticsDTO:
        statistics = await self.statistics_repository.get_statistics_by_id(
            statistics_id
        )
        return StatisticsDTO.from_orm(statistics)

    async def get_user_statistics(self, user_id: int) -> StatisticsDTO:
        user = await self.user_repository.get_user_by_id(user_id)
        statistics = await self.statistics_repository.get_user_staistics(user)
        return StatisticsDTO.from_orm(statistics)

    async def update_statistics(self, statistics_id: int) -> StatisticsDTO:
        statistics = await self.statistics_repository.get_statistics_by_id(
            statistics_id
        )
        updated_staistics = await self.statistics_repository.update_statistics(
            statistics
        )
        return StatisticsDTO.from_orm(updated_staistics)

    async def delete_statistics(self, statistics_id: int):
        statistics = await self.statistics_repository.get_statistics_by_id(
            statistics_id
        )
        await self.statistics_repository.delete_statistics(statistics)
