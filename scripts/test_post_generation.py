#!/usr/bin/env python
"""
Test script for post generation.
Creates random number of posts for testing purposes.

Usage:
    python scripts/test_post_generation.py --flow-id 1
    python scripts/test_post_generation.py --flow-id 1 --min-posts 5 --max-posts 15
    python scripts/test_post_generation.py --flow-id 1 --exact 10
"""

import argparse
import asyncio
import os
import random
import sys
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.dev')

import django
django.setup()

from django.utils import timezone
from admin_panel.models import Flow, Post
from bot.database.models import PostDTO, PostStatus


async def create_test_posts(flow_id: int, count: int):
    """Create test posts for a flow"""
    try:
        flow = await Flow.objects.aget(id=flow_id)
    except Flow.DoesNotExist:
        print(f"❌ Flow with ID {flow_id} not found!")
        return

    print(f"\n🎯 Creating {count} test posts for flow '{flow.name}' (ID: {flow_id})")
    print(f"📊 Current flow_volume setting: {flow.flow_volume}")
    print("-" * 60)

    created_count = 0
    duplicate_count = 0

    for i in range(count):
        # Generate random content
        topics = [
            "Новини технологій",
            "Цікаві факти",
            "Поради для розвитку",
            "Мотиваційні цитати",
            "Лайфхаки",
            "Наукові відкриття",
            "Бізнес-ідеї",
            "Історії успіху",
        ]

        topic = random.choice(topics)
        content = f"🔥 {topic} #{i+1}\n\n"
        content += f"Це тестовий пост, створений {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        content += "Lorem ipsum dolor sit amet, consectetur adipiscing elit. " * random.randint(1, 3)

        # Add signature if flow has one
        if flow.signature:
            content += f"\n\n{flow.signature}"

        # Generate unique source_id
        source_id = f"test_{flow_id}_{datetime.now().timestamp()}_{random.randint(1000, 9999)}"

        # Random original date (last 7 days)
        days_ago = random.randint(0, 7)
        original_date = timezone.now() - timedelta(days=days_ago)

        try:
            # Check if post with this source_id already exists
            existing = await Post.objects.filter(source_id=source_id).afirst()
            if existing:
                duplicate_count += 1
                print(f"  ⚠️  Post {i+1}/{count}: Duplicate, skipping")
                continue

            # Create post
            post = Post(
                flow=flow,
                content=content,
                status=Post.DRAFT,
                source_id=source_id,
                source_url=f"https://test.example.com/post/{i+1}",
                original_content=content[:100],
                original_date=original_date,
                original_link=f"https://test.example.com/original/{i+1}",
            )
            await post.asave()

            created_count += 1
            print(f"  ✅ Post {i+1}/{count}: Created (source_id: {source_id})")

        except Exception as e:
            print(f"  ❌ Post {i+1}/{count}: Failed - {e}")

        # Small delay to avoid overwhelming the system
        await asyncio.sleep(0.1)

    print("-" * 60)
    print(f"\n📈 Summary:")
    print(f"  Created: {created_count} posts")
    print(f"  Duplicates: {duplicate_count}")
    print(f"  Failed: {count - created_count - duplicate_count}")

    # Show current statistics
    total_drafts = await Post.objects.filter(flow=flow, status=Post.DRAFT).acount()
    total_published = await Post.objects.filter(flow=flow, status=Post.PUBLISHED).acount()
    total_scheduled = await Post.objects.filter(flow=flow, status=Post.SCHEDULED).acount()

    print(f"\n📊 Flow statistics:")
    print(f"  Total drafts: {total_drafts}")
    print(f"  Published: {total_published}")
    print(f"  Scheduled: {total_scheduled}")
    print(f"  Shown in dialog: {min(total_drafts, flow.flow_volume)} (flow_volume={flow.flow_volume})")


async def list_flows():
    """List all available flows"""
    print("\n📋 Available flows:\n")
    print(f"{'ID':<5} {'Name':<30} {'Channel':<30} {'Volume':<8} {'Drafts':<8}")
    print("-" * 90)

    async for flow in Flow.objects.select_related('channel').all():
        draft_count = await Post.objects.filter(flow=flow, status=Post.DRAFT).acount()
        print(f"{flow.id:<5} {flow.name:<30} {flow.channel.name:<30} {flow.flow_volume:<8} {draft_count:<8}")


async def delete_test_posts(flow_id: int):
    """Delete all test posts for a flow"""
    try:
        flow = await Flow.objects.aget(id=flow_id)
    except Flow.DoesNotExist:
        print(f"❌ Flow with ID {flow_id} not found!")
        return

    # Delete posts with source_id starting with "test_"
    deleted_count = await Post.objects.filter(
        flow=flow,
        source_id__startswith=f"test_{flow_id}_"
    ).adelete()

    print(f"🧹 Deleted {deleted_count[0]} test posts from flow '{flow.name}'")


def main():
    parser = argparse.ArgumentParser(
        description='Test script for post generation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create random number of posts (5-15) for flow 1
  python scripts/test_post_generation.py --flow-id 1

  # Create exact number of posts
  python scripts/test_post_generation.py --flow-id 1 --exact 10

  # Create random number within range
  python scripts/test_post_generation.py --flow-id 1 --min-posts 3 --max-posts 8

  # List all available flows
  python scripts/test_post_generation.py --list

  # Delete test posts
  python scripts/test_post_generation.py --flow-id 1 --delete
        """
    )

    parser.add_argument(
        '--flow-id',
        type=int,
        help='ID of the flow to create posts for'
    )

    parser.add_argument(
        '--exact',
        type=int,
        help='Exact number of posts to create'
    )

    parser.add_argument(
        '--min-posts',
        type=int,
        default=5,
        help='Minimum number of posts to create (default: 5)'
    )

    parser.add_argument(
        '--max-posts',
        type=int,
        default=15,
        help='Maximum number of posts to create (default: 15)'
    )

    parser.add_argument(
        '--list',
        action='store_true',
        help='List all available flows'
    )

    parser.add_argument(
        '--delete',
        action='store_true',
        help='Delete all test posts for the specified flow'
    )

    args = parser.parse_args()

    # List flows
    if args.list:
        asyncio.run(list_flows())
        return

    # Validate flow-id
    if not args.flow_id and not args.list:
        parser.error('--flow-id is required unless using --list')

    # Delete test posts
    if args.delete:
        asyncio.run(delete_test_posts(args.flow_id))
        return

    # Determine number of posts to create
    if args.exact:
        count = args.exact
        print(f"🎲 Creating exact {count} posts")
    else:
        count = random.randint(args.min_posts, args.max_posts)
        print(f"🎲 Random number selected: {count} posts (range: {args.min_posts}-{args.max_posts})")

    # Create posts
    asyncio.run(create_test_posts(args.flow_id, count))


if __name__ == '__main__':
    main()
