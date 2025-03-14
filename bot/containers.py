from dependency_injector import containers, providers
from bot.database.repositories.user_repository import UserRepository
from bot.services.user_service import UserService

class Container(containers.DeclarativeContainer):
    user_repository = providers.Factory(UserRepository)

    user_service = providers.Factory(
        UserService,
        user_repository=user_repository
    )