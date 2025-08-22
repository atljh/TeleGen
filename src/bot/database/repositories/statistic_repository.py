from admin_panel.admin_panel.models import Statistics, User
from bot.database.exceptions import StatisticsNotFoundError

class StatisticsRepository:
    async def create_statistics(self, user, channel, total_posts: int, total_views: int, total_likes: int) -> Statistics:
        return await Statistics.objects.acreate(
            user=user,
            channel=channel,
            total_posts=total_posts,
            total_views=total_views,
            total_likes=total_likes
        )

    async def get_statistics_by_id(self, statistics_id: int) -> Statistics:
        try:
            return await Statistics.objects.aget(id=statistics_id)
        except Statistics.DoesNotExist:
            raise StatisticsNotFoundError(f"Statistics with id={statistics_id} not found.")

    async def get_user_staistics(self, user: User) -> Statistics:
        try:
            return await Statistics.objects.aget(user=user)
        except Statistics.DoesNotExist:
            raise StatisticsNotFoundError(f"Statistics with user={user} not found.")

    async def update_statistics(self, statistics: Statistics) -> Statistics:
        await statistics.asave()
        return statistics

    async def delete_statistics(self, statistics: Statistics):
        await statistics.adelete()