
import pytest
import sys
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

# Добавляем корневую директорию проекта в sys.path
sys.path.append("/Users/fyodorlukashov/Music/TeleGen")

@pytest.mark.asyncio
async def test_check_flows_generation_task():
    """Тест для задачи check_flows_generation"""
    # Создаем моки для необходимых сервисов
    mock_flow_service = AsyncMock()
    mock_post_service = AsyncMock()

    # Создаем мок для потока
    mock_loop = MagicMock()
    mock_loop.run_until_complete = MagicMock()

    # Создаем мок для потока asyncio
    with patch('asyncio.new_event_loop', return_value=mock_loop),          patch('asyncio.set_event_loop') as mock_set_event_loop,          patch('bot.tasks.Container.flow_service', return_value=mock_flow_service),          patch('bot.tasks.Container.post_service', return_value=mock_post_service),          patch('bot.tasks._start_telegram_generations') as mock_start_gen,          patch('bot.tasks.logger') as mock_logger:

        # Создаем тестовые данные
        test_flow = MagicMock()
        test_flow.id = 1
        test_flow.flow_volume = 10

        mock_flow_service.get_flows_due_for_generation.return_value = [test_flow]

        # Импортируем функцию для тестирования
        from bot.tasks import check_flows_generation

        # Вызываем задачу
        check_flows_generation()

        # Проверяем, что методы были вызваны
        mock_flow_service.get_flows_due_for_generation.assert_called_once()
        mock_start_telegram_generations.assert_called_once_with(
            test_flow, mock_flow_service, mock_post_service, auto_generate=True
        )

@pytest.mark.asyncio
async def test_check_scheduled_posts_task():
    """Тест для задачи check_scheduled_posts"""
    # Создаем мок для пост-сервиса
    mock_post_service = AsyncMock()

    # Создаем мок для потока
    mock_loop = MagicMock()
    mock_loop.run_until_complete = MagicMock()

    # Создаем мок для поста
    test_post = MagicMock()
    test_post.dict.return_value = {"id": 1, "content": "Test content"}

    mock_post_service.publish_scheduled_posts.return_value = [test_post]

    # Создаем мок для потока asyncio
    with patch('asyncio.new_event_loop', return_value=mock_loop),          patch('asyncio.set_event_loop') as mock_set_event_loop,          patch('bot.tasks.Container.post_service', return_value=mock_post_service),          patch('bot.tasks.logger') as mock_logger:

        # Импортируем функцию для тестирования
        from bot.tasks import check_scheduled_posts

        # Вызываем задачу
        result = check_scheduled_posts()

        # Проверяем, что методы были вызваны
        mock_post_service.publish_scheduled_posts.assert_called_once()

        # Проверяем результат
        assert result == [{"id": 1, "content": "Test content"}]

@pytest.mark.asyncio
async def test_async_check_flows_generation():
    """Тест для асинхронной функции _async_check_flows_generation"""
    # Создаем моки для необходимых сервисов
    mock_flow_service = AsyncMock()
    mock_post_service = AsyncMock()

    # Создаем мок для потока
    with patch('bot.tasks.Container.flow_service', return_value=mock_flow_service),          patch('bot.tasks.Container.post_service', return_value=mock_post_service),          patch('bot.tasks._start_telegram_generations') as mock_start_gen,          patch('bot.tasks.logger') as mock_logger:

        # Создаем тестовые данные
        test_flow = MagicMock()
        test_flow.id = 1
        test_flow.flow_volume = 10

        mock_flow_service.get_flows_due_for_generation.return_value = [test_flow]

        # Импортируем функцию для тестирования
        from bot.tasks import _async_check_flows_generation

        # Вызываем функцию
        await _async_check_flows_generation()

        # Проверяем, что методы были вызваны
        mock_flow_service.get_flows_due_for_generation.assert_called_once()
        mock_start_telegram_generations.assert_called_once_with(
            test_flow, mock_flow_service, mock_post_service, auto_generate=True
        )

@pytest.mark.asyncio
async def test_async_check_scheduled_posts():
    """Тест для асинхронной функции _async_check_scheduled_posts"""
    # Создаем мок для пост-сервиса
    mock_post_service = AsyncMock()

    # Создаем мок для поста
    test_post = MagicMock()
    test_post.dict.return_value = {"id": 1, "content": "Test content"}

    mock_post_service.publish_scheduled_posts.return_value = [test_post]

    # Создаем мок для потока
    with patch('bot.tasks.Container.post_service', return_value=mock_post_service),          patch('bot.tasks.logger') as mock_logger:

        # Импортируем функцию для тестирования
        from bot.tasks import _async_check_scheduled_posts

        # Вызываем функцию
        result = await _async_check_scheduled_posts()

        # Проверяем, что методы были вызваны
        mock_post_service.publish_scheduled_posts.assert_called_once()

        # Проверяем результат
        assert result == [{"id": 1, "content": "Test content"}]
