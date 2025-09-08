import pytest
import asyncio
import sys
from unittest.mock import AsyncMock, patch, MagicMock
from aiogram import Bot
from aiogram.fsm.storage.memory import MemoryStorage

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

@pytest.mark.asyncio
async def test_main_successful_start(mock_container, mock_bot, mock_logger):
    with patch('main.setup_logging', return_value=mock_logger), \
         patch('main.Container', return_value=mock_container), \
         patch('main.Dispatcher') as mock_dp:
        
        dp_instance = mock_dp.return_value
        dp_instance.start_polling = AsyncMock()
        
        await main()
        
        mock_container.bot.assert_called_once()
        
        mock_logger.log.assert_not_called()
        
        assert dp_instance.update.middleware.register.called
        assert dp_instance.start_polling.called

@pytest.mark.asyncio
async def test_main_error_handling(mock_container, mock_bot, mock_logger):
    with patch('main.setup_logging', return_value=mock_logger), \
         patch('main.Container', return_value=mock_container), \
         patch('main.Dispatcher') as mock_dp, \
         patch('main.logging') as mock_logging:
        
        dp_instance = mock_dp.return_value
        test_error = Exception("Test error")
        dp_instance.start_polling.side_effect = test_error
        
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
async def test_main_disabled_telegram_logger(mock_container, mock_bot):
    with patch('main.setup_logging') as mock_setup_logging, \
         patch('main.Container', return_value=mock_container), \
         patch('main.Dispatcher') as mock_dp, \
         patch('main.logging'):
        
        mock_logger = AsyncMock()
        mock_logger.enabled = False
        mock_setup_logging.return_value = mock_logger
        
        dp_instance = mock_dp.return_value
        test_error = Exception("Test error")
        dp_instance.start_polling.side_effect = test_error
        
        with pytest.raises(Exception):
            await main()
        
        mock_logger.log.assert_not_called()

@pytest.mark.asyncio
async def test_main_shutdown_logging(mock_container, mock_bot, mock_logger):
    with patch('main.setup_logging', return_value=mock_logger), \
         patch('main.Container', return_value=mock_container), \
         patch('main.Dispatcher') as mock_dp, \
         patch('main.logging') as mock_logging:
        
        dp_instance = mock_dp.return_value
        dp_instance.start_polling = AsyncMock()
        
        await main()
        
        mock_logging.info.assert_called_once_with("Bot shutdown completed")
