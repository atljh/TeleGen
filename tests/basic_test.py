
import pytest
import asyncio
import sys
from unittest.mock import AsyncMock, patch, MagicMock

# Добавляем корневую директорию проекта в sys.path
sys.path.append("/Users/fyodorlukashov/Music/TeleGen")

# Простые тесты без сложных импортов

def test_simple_math():
    """Простой тест для проверки работы pytest"""
    assert 2 + 2 == 4

@pytest.mark.asyncio
async def test_async_function():
    """Тест для проверки работы асинхронных тестов"""
    await asyncio.sleep(0.1)
    assert True

def test_mocking():
    """Тест для проверки работы моков"""
    mock_obj = MagicMock()
    mock_obj.return_value = "test_value"
    assert mock_obj() == "test_value"

@pytest.mark.asyncio
async def test_async_mock():
    """Тест для проверки работы асинхронных моков"""
    mock_obj = AsyncMock()
    mock_obj.return_value = "async_test_value"
    assert await mock_obj() == "async_test_value"

def test_path_setup():
    """Тест для проверки, что путь к корневой директории добавлен"""
    import os
    expected_path = "/Users/fyodorlukashov/Music/TeleGen"
    assert expected_path in sys.path
