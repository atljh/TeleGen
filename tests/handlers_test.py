
import pytest
import sys
from unittest.mock import AsyncMock, patch
from aiogram import types
from aiogram.filters import Command

from bot.handlers.basic_commands import basic_commands_router
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram import Dispatcher

@pytest.fixture
def mock_dispatcher():
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    dp.include_router(basic_commands_router)
    return dp

@pytest.mark.asyncio
async def test_start_command(mock_dispatcher, fake_message):
    fake_message.answer = AsyncMock()

    await mock_dispatcher.feed_update(types.Update(
        update_id=1,
        message=fake_message
    ))

    assert fake_message.answer.called
    response_text = fake_message.answer.call_args[0][0]

    assert "👋 **Вітаємо у нашому боті!**" in response_text
    assert "Щоб почати, оберіть потрібну команду з меню або введіть /help" in response_text

@pytest.mark.asyncio
async def test_help_command(mock_dispatcher, fake_message):
    fake_message.answer = AsyncMock()

    await mock_dispatcher.feed_update(types.Update(
        update_id=1,
        message=fake_message
    ))

    assert fake_message.answer.called

    response_text = fake_message.answer.call_args[0][0]
    assert "🆘 **Допомога**" in response_text
    assert "/start - Початок роботи" in response_text
    assert "/settings - Налаштування" in response_text
    assert "/price - Переглянути ціни" in response_text

@pytest.mark.asyncio
async def test_settings_command(mock_dispatcher, fake_message):
    fake_message.answer = AsyncMock()

    await mock_dispatcher.feed_update(types.Update(
        update_id=1,
        message=fake_message
    ))

    assert fake_message.answer.called

    response_text = fake_message.answer.call_args[0][0]
    assert "⚙ **Налаштування бота**" in response_text
    assert "Мову інтерфейсу" in response_text
    assert "Сповіщення" in response_text
    assert "Особисті параметри" in response_text

@pytest.mark.asyncio
async def test_price_command(mock_dispatcher, fake_message):
    fake_message.answer = AsyncMock()

    await mock_dispatcher.feed_update(types.Update(
        update_id=1,
        message=fake_message
    ))

    assert fake_message.answer.called

    response_text = fake_message.answer.call_args[0][0]
    assert "💵 **Наші ціни**" in response_text
    assert "🔹 Базовий тариф - 100 грн/міс" in response_text
    assert "🔹 Стандартний тариф - 200 грн/міс" in response_text
    assert "🔹 Преміум тариф - 350 грн/міс" in response_text

@pytest.mark.asyncio
async def test_menu_command(mock_dispatcher, fake_message):
    fake_message.answer = AsyncMock()

    await mock_dispatcher.feed_update(types.Update(
        update_id=1,
        message=fake_message
    ))

    assert fake_message.answer.called

    response_text = fake_message.answer.call_args[0][0]
    assert "📱 **Головне меню**" in response_text
    assert "Оберіть потрібний пункт:" in response_text

    call_args = fake_message.answer.call_args
    assert 'reply_markup' in call_args.kwargs
    keyboard = call_args.kwargs['reply_markup']
    assert keyboard is not None
    assert len(keyboard.keyboard) == 3
    assert "⚙ Налаштування" in keyboard.keyboard[0][0].text
    assert "🆘 Допомога" in keyboard.keyboard[1][0].text
    assert "💵 Ціни" in keyboard.keyboard[2][0].text
