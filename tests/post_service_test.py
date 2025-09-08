
import pytest
import sys
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram import Bot

from bot.services.post.post_service import PostService
from bot.database.repositories import PostRepository, FlowRepository
from bot.database.models import PostDTO, PostStatus
from bot.database.exceptions import PostNotFoundError, InvalidOperationError
from bot.services.web.web_service import WebService
from bot.services.telegram_userbot import EnhancedUserbotService

@pytest.fixture
def mock_bot():
    return AsyncMock(spec=Bot)

@pytest.fixture
def mock_web_service():
    return AsyncMock(spec=WebService)

@pytest.fixture
def mock_userbot_service():
    return AsyncMock(spec=EnhancedUserbotService)

@pytest.fixture
def mock_post_repository():
    return AsyncMock(spec=PostRepository)

@pytest.fixture
def mock_flow_repository():
    return AsyncMock(spec=FlowRepository)

@pytest.fixture
def post_service(
    mock_bot, 
    mock_web_service, 
    mock_userbot_service, 
    mock_post_repository, 
    mock_flow_repository
):
    return PostService(
        bot=mock_bot,
        web_service=mock_web_service,
        userbot_service=mock_userbot_service,
        post_repository=mock_post_repository,
        flow_repository=mock_flow_repository,
    )

@pytest.mark.asyncio
async def test_get_post(post_service, mock_post_repository):
    test_post = PostDTO(
        id=1,
        flow_id=1,
        content="Test content",
        status=PostStatus.DRAFT,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    mock_post_repository.get.return_value = test_post

    result = await post_service.get_post(1)

    assert result == test_post
    mock_post_repository.get.assert_called_once_with(1)

@pytest.mark.asyncio
async def test_update_post(post_service, mock_post_repository):
    test_post = PostDTO(
        id=1,
        flow_id=1,
        content="Old content",
        status=PostStatus.DRAFT,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    updated_post = PostDTO(
        id=1,
        flow_id=1,
        content="New content",
        status=PostStatus.PUBLISHED,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    mock_post_repository.update.return_value = updated_post

    result = await post_service.update_post(1, content="New content", status=PostStatus.PUBLISHED)

    assert result == updated_post
    mock_post_repository.update.assert_called_once_with(
        1, content="New content", status=PostStatus.PUBLISHED
    )

@pytest.mark.asyncio
async def test_delete_post(post_service, mock_post_repository):
    mock_post_repository.delete.return_value = None

    await post_service.delete_post(1)

    mock_post_repository.delete.assert_called_once_with(1)

@pytest.mark.asyncio
async def test_publish_post(post_service):
    test_post = PostDTO(
        id=1,
        flow_id=1,
        content="Test content",
        status=PostStatus.DRAFT,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    published_post = PostDTO(
        id=1,
        flow_id=1,
        content="Test content",
        status=PostStatus.PUBLISHED,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    post_service.publishing_service.publish_post.return_value = published_post

    result = await post_service.publish_post(1, "test_channel")

    assert result == published_post
    post_service.publishing_service.publish_post.assert_called_once_with(1, "test_channel")

@pytest.mark.asyncio
async def test_schedule_post(post_service):
    scheduled_time = datetime(2023, 12, 31, 23, 59, 59)
    test_post = PostDTO(
        id=1,
        flow_id=1,
        content="Test content",
        status=PostStatus.SCHEDULED,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    post_service.scheduling_service.schedule_post.return_value = test_post

    result = await post_service.schedule_post(1, scheduled_time)

    assert result == test_post
    post_service.scheduling_service.schedule_post.assert_called_once_with(1, scheduled_time)

@pytest.mark.asyncio
async def test_publish_scheduled_posts(post_service):
    test_posts = [
        PostDTO(
            id=1,
            flow_id=1,
            content="Test content 1",
            status=PostStatus.SCHEDULED,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
        PostDTO(
            id=2,
            flow_id=1,
            content="Test content 2",
            status=PostStatus.SCHEDULED,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
    ]

    post_service.scheduling_service.publish_scheduled_posts.return_value = test_posts

    result = await post_service.publish_scheduled_posts()

    assert result == test_posts
    post_service.scheduling_service.publish_scheduled_posts.assert_called_once()

@pytest.mark.asyncio
async def test_generate_auto_posts(post_service):
    test_posts = [
        PostDTO(
            id=1,
            flow_id=1,
            content="Generated content 1",
            status=PostStatus.DRAFT,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
        PostDTO(
            id=2,
            flow_id=1,
            content="Generated content 2",
            status=PostStatus.DRAFT,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
    ]

    post_service.generation_service.generate_auto_posts.return_value = test_posts

    result = await post_service.generate_auto_posts(1, auto_generate=True)

    assert result == test_posts
    post_service.generation_service.generate_auto_posts.assert_called_once_with(1, True)

@pytest.mark.asyncio
async def test_create_post_success(post_service, mock_flow_repository):
    flow_id = 1
    content = "Test content"
    original_link = "https://example.com"
    original_date = datetime.now()
    original_content = "Original content"
    scheduled_time = datetime(2023, 12, 31, 23, 59, 59)

    test_post = PostDTO(
        id=1,
        flow_id=flow_id,
        content=content,
        status=PostStatus.DRAFT,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    mock_flow_repo = post_service.flow_repo
    mock_flow_repo.exists.return_value = True
    mock_flow_repo.get_flow_by_id.return_value = MagicMock(id=flow_id)
    mock_flow_repo.post_repo.create_with_media.return_value = test_post

    result = await post_service.create_post(
        flow_id=flow_id,
        content=content,
        original_link=original_link,
        original_date=original_date,
        original_content=original_content,
        scheduled_time=scheduled_time,
    )

    assert result == test_post
    mock_flow_repo.exists.assert_called_once_with(flow_id)
    mock_flow_repo.get_flow_by_id.assert_called_once_with(flow_id)
    mock_flow_repo.post_repo.create_with_media.assert_called_once()

@pytest.mark.asyncio
async def test_create_post_flow_not_found(post_service, mock_flow_repository):
    flow_id = 999
    mock_flow_repo = post_service.flow_repo
    mock_flow_repo.exists.return_value = False

    with pytest.raises(PostNotFoundError) as exc_info:
        await post_service.create_post(
            flow_id=flow_id,
            content="Test content",
            original_link="https://example.com",
            original_date=datetime.now(),
            original_content="Original content",
        )

    assert f"Flow with id {flow_id} not found" in str(exc_info.value)
    mock_flow_repo.exists.assert_called_once_with(flow_id)

@pytest.mark.asyncio
async def test_create_post_past_scheduled_time(post_service, mock_flow_repository):
    flow_id = 1
    scheduled_time = datetime(2022, 1, 1, 0, 0, 0)
    mock_flow_repo = post_service.flow_repo
    mock_flow_repo.exists.return_value = True

    with pytest.raises(InvalidOperationError) as exc_info:
        await post_service.create_post(
            flow_id=flow_id,
            content="Test content",
            original_link="https://example.com",
            original_date=datetime.now(),
            original_content="Original content",
            scheduled_time=scheduled_time,
        )

    assert "Scheduled time cannot be in the past" in str(exc_info.value)
    mock_flow_repo.exists.assert_called_once_with(flow_id)
