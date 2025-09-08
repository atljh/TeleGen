
import pytest
import sys
from unittest.mock import AsyncMock, patch, MagicMock
from aiogram import Bot
from aiogram.client.session.aiohttp import AiohttpSession

from bot.containers import Container
from bot.services.telegram_userbot import EnhancedUserbotService
from bot.services.post.post_service import PostService
from bot.services.web.web_service import WebService

@pytest.fixture
def mock_session():
    return AsyncMock(spec=AiohttpSession)

@pytest.fixture
def mock_bot(mock_session):
    return AsyncMock(spec=Bot, session=mock_session)

@pytest.fixture
def mock_container(mock_bot):
    with patch('os.getenv', side_effect=lambda key: {
        "TELEGRAM_BOT_TOKEN": "test_token",
        "USERBOT_API_ID": "123",
        "USERBOT_API_HASH": "test_hash",
        "TELEGRAM_PHONE": "+1234567890",
        "OPENAI_API_KEY": "test_key",
        "RSS_API_KEY": "test_rss_key",
        "RSS_API_SECRET": "test_rss_secret",
    }.get(key)):
        container = Container()
        container.bot.override(mock_bot)
        return container

@pytest.mark.asyncio
async def test_container_bot_creation(mock_container):
    bot = mock_container.bot()
    assert bot == mock_container.bot._instance

@pytest.mark.asyncio
async def test_container_userbot_service_creation(mock_container):
    userbot_service = mock_container.userbot_service()
    assert isinstance(userbot_service, EnhancedUserbotService)

@pytest.mark.asyncio
async def test_container_post_service_creation(mock_container):
    post_service = mock_container.post_service()
    assert isinstance(post_service, PostService)

@pytest.mark.asyncio
async def test_container_web_service_creation(mock_container):
    web_service = mock_container.web_service()
    assert isinstance(web_service, WebService)

@pytest.mark.asyncio
async def test_container_shutdown_resources(mock_container):
    mock_session = mock_container.session()
    mock_userbot_service = mock_container.userbot_service()

    await mock_container.shutdown_resources()

    mock_session.close.assert_called_once()

    mock_userbot_service.stop.assert_called_once()

@pytest.mark.asyncio
async def test_container_wiring_configuration(mock_container):
    assert mock_container.wiring_config is not None
    assert hasattr(mock_container.wiring_config, 'modules')
    assert len(mock_container.wiring_config.modules) > 0
