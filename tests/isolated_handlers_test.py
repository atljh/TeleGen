
import pytest
import sys
from unittest.mock import AsyncMock, patch
from aiogram import types
from aiogram.filters import Command

# Добавляем корневую директорию проекта в sys.path
sys.path.append("/Users/fyodorlukashov/Music/TeleGen")

# Импортируем только необходимые части напрямую, чтобы избежать циклических импортов
from bot.handlers.basic_commands import basic_commands_router

@pytest.fixture
def mock_message():
    message = AsyncMock(spec=types.Message)
    message.answer = AsyncMock()
    message.text = "/start"
    return message

@pytest.fixture
def mock_update(mock_message):
    update = AsyncMock(spec=types.Update)
    update.message = mock_message
    return update

@pytest.mark.asyncio
async def test_start_command_handler(mock_update):
    # Создаем роутер с обработчиками
    router = basic_commands_router

    # Находим обработчик для команды /start
    start_handler = None
    for handler in router.update_handlers.handlers:
        if hasattr(handler, 'filters') and Command("start") in handler.filters:
            start_handler = handler.callback
            break

    # Проверяем, что обработчик найден
    assert start_handler is not None

    # Вызываем обработчик
    await start_handler(mock_update.message)

    # Проверяем, что метод answer был вызван
    mock_update.message.answer.assert_called_once()

    # Проверяем, что в ответе есть ожидаемый текст
    response_text = mock_update.message.answer.call_args[0][0]
    assert "👋 **Вітаємо у нашому боті!**" in response_text
    assert "Щоб почати, оберіть потрібну команду з меню або введіть /help" in response_text

@pytest.mark.asyncio
async def test_help_command_handler(mock_update):
    # Создаем роутер с обработчиками
    router = basic_commands_router

    # Находим обработчик для команды /help
    help_handler = None
    for handler in router.update_handlers.handlers:
        if hasattr(handler, 'filters') and Command("help") in handler.filters:
            help_handler = handler.callback
            break

    # Проверяем, что обработчик найден
    assert help_handler is not None

    # Вызываем обработчик
    await help_handler(mock_update.message)

    # Проверяем, что метод answer был вызван
    mock_update.message.answer.assert_called_once()

    # Проверяем, что в ответе есть ожидаемый текст
    response_text = mock_update.message.answer.call_args[0][0]
    assert "🆘 **Допомога**" in response_text
    assert "/start - Початок роботи" in response_text
    assert "/settings - Налаштування" in response_text
    assert "/price - Переглянути ціни" in response_text

@pytest.mark.asyncio
async def test_settings_command_handler(mock_update):
    # Создаем роутер с обработчиками
    router = basic_commands_router

    # Находим обработчик для команды /settings
    settings_handler = None
    for handler in router.update_handlers.handlers:
        if hasattr(handler, 'filters') and Command("settings") in handler.filters:
            settings_handler = handler.callback
            break

    # Проверяем, что обработчик найден
    assert settings_handler is not None

    # Вызываем обработчик
    await settings_handler(mock_update.message)

    # Проверяем, что метод answer был вызван
    mock_update.message.answer.assert_called_once()

    # Проверяем, что в ответе есть ожидаемый текст
    response_text = mock_update.message.answer.call_args[0][0]
    assert "⚙ **Налаштування бота**" in response_text
    assert "Мову інтерфейсу" in response_text
    assert "Сповіщення" in response_text
    assert "Особисті параметри" in response_text

@pytest.mark.asyncio
async def test_price_command_handler(mock_update):
    # Создаем роутер с обработчиками
    router = basic_commands_router

    # Находим обработчик для команды /price
    price_handler = None
    for handler in router.update_handlers.handlers:
        if hasattr(handler, 'filters') and Command("price") in handler.filters:
            price_handler = handler.callback
            break

    # Проверяем, что обработчик найден
    assert price_handler is not None

    # Вызываем обработчик
    await price_handler(mock_update.message)

    # Проверяем, что метод answer был вызван
    mock_update.message.answer.assert_called_once()

    # Проверяем, что в ответе есть ожидаемый текст
    response_text = mock_update.message.answer.call_args[0][0]
    assert "💵 **Наші ціни**" in response_text
    assert "🔹 Базовий тариф - 100 грн/міс" in response_text
    assert "🔹 Стандартний тариф - 200 грн/міс" in response_text
    assert "🔹 Преміум тариф - 350 грн/міс" in response_text
