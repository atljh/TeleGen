import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram import Bot

from bot.main import main

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


@pytest.fixture
def mock_bot():
    return AsyncMock(spec=Bot)


@pytest.fixture
def mock_container(mock_bot):
    container = MagicMock()
    container.bot.return_value = mock_bot
    return container


@pytest.fixture
def mock_logger():
    logger = AsyncMock()
    logger.enabled = True
    return logger


@pytest.mark.asyncio
async def test_main_successful_start(mock_container, mock_bot, mock_logger):
    with patch("bot.main.setup_logging", return_value=mock_logger), patch(
        "bot.main.Container", return_value=mock_container
    ), patch("bot.main.Dispatcher") as mock_dp:
        dp_instance = mock_dp.return_value
        dp_instance.start_polling = AsyncMock()

        dp_instance.update = MagicMock()
        dp_instance.update.middleware = MagicMock()
        dp_instance.update.middleware.register = MagicMock()

        await main()

        mock_container.bot.assert_called_once()
        mock_logger.log.assert_not_called()
        assert dp_instance.update.middleware.register.called
        assert dp_instance.start_polling.called
