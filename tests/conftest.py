import pytest
from unittest.mock import AsyncMock, MagicMock
from aiogram import Bot, Dispatcher
from aiogram.types import User, Chat, Message, Update

@pytest.fixture
def mock_bot():
    bot = AsyncMock(spec=Bot)
    bot.send_message = AsyncMock()
    bot.send_photo = AsyncMock()
    return bot

@pytest.fixture
def mock_dispatcher():
    return Dispatcher()

@pytest.fixture
def fake_user():
    return User(
        id=123456789,
        is_bot=False,
        first_name="Test",
        last_name="User",
        username="testuser"
    )

@pytest.fixture
def fake_chat():
    return Chat(
        id=123456789,
        type="private",
        title=None,
        username="testuser"
    )

@pytest.fixture
def fake_message(fake_user, fake_chat):
    return Message(
        message_id=1,
        from_user=fake_user,
        chat=fake_chat,
        date=None,
        text="/start"
    )
    