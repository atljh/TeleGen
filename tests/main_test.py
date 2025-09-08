
import pytest
import asyncio
import sys
from unittest.mock import AsyncMock, patch, MagicMock
from aiogram import Bot
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram import Dispatcher

from bot.containers import Container
from bot.main import main
from bot.services.logger_service import LogEvent, LogLevel

@pytest.fixture
def mock_bot():
    return AsyncMock(spec=Bot)

@pytest.fixture
def mock_container(mock_bot):
    container = MagicMock(spec=Container)
    container.bot.return_value = mock_bot
    return container

@pytest.fixture
def mock_logger():
    logger = AsyncMock()
    logger.enabled = True
    return logger

@pytest.fixture
def mock_dp():
    dp = AsyncMock(spec=Dispatcher)
    dp.update.middleware.register = MagicMock()
    dp.start_polling = AsyncMock()
    return dp

@pytest.mark.asyncio
async def test_main_successful_start(mock_container, mock_bot, mock_logger, mock_dp):
    with patch('bot.main.setup_logging', return_value=mock_logger),          patch('bot.main.Container', return_value=mock_container),          patch('bot.main.Dispatcher', return_value=mock_dp):

        await main()

        mock_container.bot.assert_called_once()

        mock_logger.log.assert_not_called()

        assert mock_dp.update.middleware.register.called
        assert mock_dp.start_polling.called

@pytest.mark.asyncio
async def test_main_error_handling(mock_container, mock_bot, mock_logger, mock_dp):
    with patch('bot.main.setup_logging', return_value=mock_logger),          patch('bot.main.Container', return_value=mock_container),          patch('bot.main.Dispatcher', return_value=mock_dp),          patch('bot.main.logging') as mock_logging:

        test_error = Exception("Test error")
        mock_dp.start_polling.side_effect = test_error

        with pytest.raises(Exception) as exc_info:
            await main()

        assert exc_info.value == test_error

        mock_logging.error.assert_called_once_with(f"Bot stopped with error: {test_error}")

        mock_logger.log.assert_called_once_with(
            LogEvent(
                level=LogLevel.ERROR,
                message="Bot stopped unexpectedly",
                additional_data={"Error": str(test_error), "Status": "Offline"}
            )
        )

@pytest.mark.asyncio
async def test_main_disabled_telegram_logger(mock_container, mock_bot, mock_dp):
    with patch('bot.main.setup_logging') as mock_setup_logging,          patch('bot.main.Container', return_value=mock_container),          patch('bot.main.Dispatcher', return_value=mock_dp),          patch('bot.main.logging'):

        mock_logger = AsyncMock()
        mock_logger.enabled = False
        mock_setup_logging.return_value = mock_logger

        test_error = Exception("Test error")
        mock_dp.start_polling.side_effect = test_error

        with pytest.raises(Exception):
            await main()

        mock_logger.log.assert_not_called()

@pytest.mark.asyncio
async def test_main_shutdown_logging(mock_container, mock_bot, mock_logger, mock_dp):
    with patch('bot.main.setup_logging', return_value=mock_logger),          patch('bot.main.Container', return_value=mock_container),          patch('bot.main.Dispatcher', return_value=mock_dp),          patch('bot.main.logging') as mock_logging:

        await main()

        mock_logging.info.assert_called_once_with("Bot shutdown completed")

@pytest.mark.asyncio
async def test_main_container_initialization(mock_container, mock_bot, mock_logger, mock_dp):
    with patch('bot.main.setup_logging', return_value=mock_logger),          patch('bot.main.Container', return_value=mock_container),          patch('bot.main.Dispatcher', return_value=mock_dp):

        await main()

        mock_container.bot.assert_called_once()

        assert isinstance(mock_dp.storage, MemoryStorage)

        assert mock_dp.update.middleware.register.called
