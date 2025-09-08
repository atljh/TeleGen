import logging
import os
import random
from datetime import datetime
from typing import Any, list

from faker import Faker

from admin_panel.models import User

from .source_lists import TELEGRAM_SOURCES, WEB_SOURCES

logger = logging.getLogger(__name__)


class TestDataGenerator:
    def __init__(self):
        self.fake = Faker()

        self.telegram_channels = WEB_SOURCES
        self.web_sources = TELEGRAM_SOURCES

    async def _setup_django(self):
        try:
            import django
            from django.conf import settings

            if not settings.configured:
                os.environ.setdefault(
                    "DJANGO_SETTINGS_MODULE", "admin_panel.core.settings"
                )
                django.setup()

        except Exception as e:
            logger.error(f"Error setting up Django: {e}")
            raise

    async def create_test_users(self, count: int = 10) -> list[Any]:
        await self._setup_django()

        from asgiref.sync import sync_to_async

        users = []

        for i in range(count):
            try:
                username = f"test_user_{i}_{self.fake.user_name()}"
                telegram_id = random.randint(1, 999999)

                user, created = await sync_to_async(User.objects.get_or_create)(
                    username=username,
                    defaults={
                        "telegram_id": telegram_id,
                    },
                )

                if created:
                    logger.info(f"Created test user: {username}")
                else:
                    logger.info(f"User already exists: {username}")

                users.append(user)

            except Exception as e:
                logger.error(f"Error creating user {i}: {e}")

        return users

    async def create_test_channels_for_user(
        self, user: Any, min_channels: int = 1, max_channels: int = 3
    ) -> list[Any]:
        await self._setup_django()

        from asgiref.sync import sync_to_async

        from admin_panel.models import Channel

        channels = []
        num_channels = random.randint(min_channels, max_channels)

        for i in range(num_channels):
            try:
                channel_name = f"Test Channel {self.fake.word().capitalize()} {i}"
                channel_id = f"test_channel_{user.id}_{i}_{random.randint(1000, 9999)}"

                channel, created = await sync_to_async(Channel.objects.get_or_create)(
                    channel_id=channel_id,
                    defaults={
                        "user": user,
                        "name": channel_name,
                        "description": self.fake.sentence(),
                        "is_active": True,
                    },
                )

                if created:
                    logger.info(
                        f"Created channel: {channel_name} for user {user.username}"
                    )
                    channels.append(channel)

            except Exception as e:
                logger.error(f"Error creating channel for user {user.username}: {e}")

        return channels

    async def create_test_flows_for_channel(
        self, channel: Any, min_flows: int = 1, max_flows: int = 2
    ) -> list[Any]:
        await self._setup_django()

        from asgiref.sync import sync_to_async

        from admin_panel.models import Flow

        flows = []
        num_flows = random.randint(min_flows, max_flows)

        for i in range(num_flows):
            try:
                flow_name = f"Test Flow {self.fake.word().capitalize()} {i}"
                flow_volume = random.randint(5, 20)

                flow = await sync_to_async(Flow.objects.create)(
                    name=flow_name,
                    flow_volume=flow_volume,
                    channel=channel,
                    content_length="to_300",
                    frequency="hourly",
                    signature=self.fake.sentence(),
                )

                logger.info(f"Created flow: {flow_name} for channel {channel.name}")
                flows.append(flow)

            except Exception as e:
                logger.error(f"Error creating flow for channel {channel.name}: {e}")

        return flows

    async def add_test_sources_to_flow(
        self, flow: Any, min_sources: int = 2, max_sources: int = 5
    ) -> list[dict]:
        sources = []
        num_sources = random.randint(min_sources, max_sources)

        for i in range(num_sources):
            try:
                source_type = random.choice(["telegram", "web"])

                if source_type == "telegram":
                    source = {
                        "link": random.choice(self.telegram_channels),
                        "type": "telegram",
                        "added_at": datetime.now().isoformat(),
                    }
                else:
                    source = {
                        "link": random.choice(self.web_sources),
                        "type": "web",
                        "added_at": datetime.now().isoformat(),
                    }

                sources.append(source)

            except Exception as e:
                logger.error(f"Error creating source for flow {flow.name}: {e}")

        try:
            from asgiref.sync import sync_to_async

            flow.sources = sources
            await sync_to_async(flow.save)()
            logger.info(f"Added {len(sources)} sources to flow {flow.name}")

        except Exception as e:
            logger.error(f"Error updating flow with sources: {e}")

        return sources

    async def generate_complete_test_data(
        self,
        user_count: int = 5,
        min_channels_per_user: int = 1,
        max_channels_per_user: int = 3,
        min_flows_per_channel: int = 1,
        max_flows_per_channel: int = 2,
        min_sources_per_flow: int = 2,
        max_sources_per_flow: int = 5,
    ) -> dict:
        logger.info(f"Starting test data generation for {user_count} users...")

        results = {"users": [], "channels": [], "flows": [], "sources": 0}

        try:
            users = await self.create_test_users(user_count)
            results["users"] = users

            for user in users:
                channels = await self.create_test_channels_for_user(
                    user, min_channels_per_user, max_channels_per_user
                )
                results["channels"].extend(channels)

                for channel in channels:
                    flows = await self.create_test_flows_for_channel(
                        channel, min_flows_per_channel, max_flows_per_channel
                    )
                    results["flows"].extend(flows)

                    for flow in flows:
                        sources = await self.add_test_sources_to_flow(
                            flow, min_sources_per_flow, max_sources_per_flow
                        )
                        results["sources"] += len(sources)

            logger.info(
                f"Test data generation completed: "
                f"{len(results['users'])} users, "
                f"{len(results['channels'])} channels, "
                f"{len(results['flows'])} flows, "
                f"{results['sources']} sources"
            )

        except Exception as e:
            logger.error(f"Error in test data generation: {e}")
            raise

        return results

    async def cleanup_test_data(self, username_prefix: str = "test_user_") -> int:
        try:
            await self._setup_django()

            from asgiref.sync import sync_to_async

            users_to_delete = await sync_to_async(list)(
                User.objects.filter(username__startswith=username_prefix)
            )

            deleted_count = 0
            for user in users_to_delete:
                try:
                    await sync_to_async(user.delete)()
                    deleted_count += 1
                except Exception as e:
                    logger.error(f"Error deleting user {user.username}: {e}")

            logger.info(f"Cleaned up {deleted_count} test users")
            return deleted_count

        except Exception as e:
            logger.error(f"Error cleaning up test data: {e}")
            return 0


async def generate_test_data(
    user_count: int = 5,
    min_channels: int = 1,
    max_channels: int = 3,
    min_flows: int = 1,
    max_flows: int = 2,
    min_sources: int = 2,
    max_sources: int = 5,
):
    generator = TestDataGenerator()
    return await generator.generate_complete_test_data(
        user_count,
        min_channels,
        max_channels,
        min_flows,
        max_flows,
        min_sources,
        max_sources,
    )


async def cleanup_test_data():
    generator = TestDataGenerator()
    return await generator.cleanup_test_data()
