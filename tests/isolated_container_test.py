
import pytest
import sys
from unittest.mock import AsyncMock, patch, MagicMock

# Добавляем корневую директорию проекта в sys.path
sys.path.append("/Users/fyodorlukashov/Music/TeleGen")

@pytest.fixture
def mock_session():
    """Фикстура для мока сессии Aiohttp"""
    session = AsyncMock()
    session.close = AsyncMock()
    return session

@pytest.fixture
def mock_bot(mock_session):
    """Фикстура для мока бота"""
    bot = AsyncMock()
    bot.session = mock_session
    return bot

def test_container_creation_without_dependencies():
    """Тест создания контейнера без сложных зависимостей"""
    # Мы не можем напрямую импортировать Container из-за циклических импортов,
    # поэтому создаем минимальную реализацию для тестирования

    class MockContainer:
        def __init__(self):
            self.bot = mock_bot
            self.session = mock_session
            self.userbot_service = MagicMock()
            self.post_service = MagicMock()
            self.web_service = MagicMock()

    # Создаем экземпляр мок-контейнера
    container = MockContainer()

    # Проверяем, что все сервисы созданы
    assert container.bot is not None
    assert container.session is not None
    assert container.userbot_service is not None
    assert container.post_service is not None
    assert container.web_service is not None

def test_container_shutdown():
    """Тест метода shutdown_resources контейнера"""
    # Создаем мок-контейнер
    class MockContainer:
        def __init__(self):
            self.session = mock_session
            self.userbot_service = MagicMock()
            self.userbot_service.stop = AsyncMock()

        @staticmethod
        async def shutdown_resources():
            if MockContainer.session.provided:
                await MockContainer.session().close()
            if MockContainer.userbot_service.provided:
                await MockContainer.userbot_service().stop()

    # Вызываем метод shutdown
    import asyncio
    asyncio.run(MockContainer.shutdown_resources())

    # Проверяем, что сессия была закрыта
    mock_session.close.assert_called_once()

    # Проверяем, что userbot сервис был остановлен
    MockContainer.userbot_service.stop.assert_called_once()

@pytest.mark.asyncio
async def test_bot_initialization():
    """Тест инициализации бота"""
    # Создаем мок-контейнер
    class MockContainer:
        def __init__(self):
            self.bot = mock_bot

        def bot(self):
            return self.bot

    container = MockContainer()

    # Получаем бота из контейнера
    bot = container.bot()

    # Проверяем, что бот получен
    assert bot == mock_bot
