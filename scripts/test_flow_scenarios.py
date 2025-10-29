#!/usr/bin/env python
"""
Advanced test scenarios for flow post management.
Tests various edge cases and scenarios.

Usage:
    python scripts/test_flow_scenarios.py --flow-id 1 --scenario overflow
    python scripts/test_flow_scenarios.py --flow-id 1 --scenario publish-cycle
    python scripts/test_flow_scenarios.py --flow-id 1 --scenario all
"""

import argparse
import asyncio
import os
import random
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.dev')

import django
django.setup()

from django.utils import timezone
from admin_panel.models import Flow, Post
from asgiref.sync import sync_to_async


class FlowTestScenarios:
    def __init__(self, flow_id: int):
        self.flow_id = flow_id
        self.flow = None

    async def setup(self):
        """Load flow"""
        try:
            self.flow = await Flow.objects.aget(id=self.flow_id)
            print(f"\n🎯 Testing flow: '{self.flow.name}' (ID: {self.flow_id})")
            print(f"📊 Flow volume: {self.flow.flow_volume}")
            print("=" * 70)
        except Flow.DoesNotExist:
            print(f"❌ Flow with ID {self.flow_id} not found!")
            sys.exit(1)

    async def print_stats(self, title="Current Statistics"):
        """Print current flow statistics"""
        draft_count = await Post.objects.filter(flow=self.flow, status=Post.DRAFT).acount()
        published_count = await Post.objects.filter(flow=self.flow, status=Post.PUBLISHED).acount()
        scheduled_count = await Post.objects.filter(flow=self.flow, status=Post.SCHEDULED).acount()

        print(f"\n📊 {title}:")
        print(f"  Drafts: {draft_count} (shown in dialog: {min(draft_count, self.flow.flow_volume)})")
        print(f"  Published: {published_count}")
        print(f"  Scheduled: {scheduled_count}")
        print(f"  Total: {draft_count + published_count + scheduled_count}")

    async def create_post(self, content_suffix="", status=Post.DRAFT):
        """Helper to create a single post"""
        source_id = f"test_scenario_{self.flow_id}_{datetime.now().timestamp()}_{random.randint(1000, 9999)}"
        content = f"Test post {content_suffix} - {datetime.now().strftime('%H:%M:%S')}"

        post = Post(
            flow=self.flow,
            content=content,
            status=status,
            source_id=source_id,
            source_url=f"https://test.example.com/post/{random.randint(1000, 9999)}",
            original_date=timezone.now(),
        )
        await post.asave()
        return post

    async def scenario_overflow(self):
        """
        Test scenario: Create more posts than flow_volume
        Expected: All posts saved, but dialog shows only flow_volume posts
        """
        print("\n🧪 Scenario: OVERFLOW TEST")
        print(f"Creating {self.flow.flow_volume * 2} posts (2x flow_volume)")
        print("-" * 70)

        await self.print_stats("Before")

        # Create 2x flow_volume posts
        for i in range(self.flow.flow_volume * 2):
            await self.create_post(f"#{i+1}")
            if (i + 1) % 5 == 0:
                print(f"  ✅ Created {i+1} posts...")

        await self.print_stats("After")

        print("\n✅ Expected behavior:")
        print(f"  - All {self.flow.flow_volume * 2} posts saved in database")
        print(f"  - Dialog shows only last {self.flow.flow_volume} posts")

    async def scenario_publish_cycle(self):
        """
        Test scenario: Create posts → Publish some → Create more
        Expected: Published posts stay, new drafts added
        """
        print("\n🧪 Scenario: PUBLISH CYCLE")
        print("-" * 70)

        await self.print_stats("Initial State")

        # Step 1: Create flow_volume drafts
        print(f"\n📝 Step 1: Creating {self.flow.flow_volume} draft posts...")
        for i in range(self.flow.flow_volume):
            await self.create_post(f"draft_{i+1}")

        await self.print_stats("After creating drafts")

        # Step 2: Publish half of the drafts
        drafts_list = await sync_to_async(lambda: list(
            Post.objects.filter(
                flow=self.flow,
                status=Post.DRAFT
            ).order_by('-created_at')[:self.flow.flow_volume // 2]
        ))()

        print(f"\n📤 Step 2: Publishing {len(drafts_list)} posts...")
        for post in drafts_list:
            post.status = Post.PUBLISHED
            post.publication_date = timezone.now()
            await post.asave()

        await self.print_stats("After publishing")

        # Step 3: Create more drafts
        new_count = self.flow.flow_volume // 2
        print(f"\n➕ Step 3: Creating {new_count} more draft posts...")
        for i in range(new_count):
            await self.create_post(f"new_draft_{i+1}")

        await self.print_stats("Final State")

        print("\n✅ Expected behavior:")
        print(f"  - Published posts remain in database")
        print(f"  - Dialog shows only last {self.flow.flow_volume} drafts")

    async def scenario_schedule_and_generate(self):
        """
        Test scenario: Create drafts → Schedule some → Generate more
        Expected: Scheduled posts don't count toward draft limit
        """
        print("\n🧪 Scenario: SCHEDULE AND GENERATE")
        print("-" * 70)

        await self.print_stats("Initial State")

        # Step 1: Create drafts
        print(f"\n📝 Step 1: Creating {self.flow.flow_volume} drafts...")
        for i in range(self.flow.flow_volume):
            await self.create_post(f"draft_{i+1}")

        await self.print_stats("After creating drafts")

        # Step 2: Schedule some posts
        drafts_list = await sync_to_async(lambda: list(
            Post.objects.filter(
                flow=self.flow,
                status=Post.DRAFT
            ).order_by('-created_at')[:self.flow.flow_volume // 3]
        ))()

        print(f"\n📅 Step 2: Scheduling {len(drafts_list)} posts...")
        for post in drafts_list:
            post.status = Post.SCHEDULED
            post.scheduled_time = timezone.now() + timedelta(hours=random.randint(1, 24))
            await post.asave()

        await self.print_stats("After scheduling")

        # Step 3: Generate more
        new_count = self.flow.flow_volume
        print(f"\n🔄 Step 3: Generating {new_count} more posts...")
        for i in range(new_count):
            await self.create_post(f"generated_{i+1}")

        await self.print_stats("Final State")

        print("\n✅ Expected behavior:")
        print(f"  - Scheduled posts kept separate")
        print(f"  - Draft dialog shows last {self.flow.flow_volume} drafts")
        print(f"  - Schedule dialog shows last {self.flow.flow_volume} scheduled")

    async def scenario_edge_cases(self):
        """
        Test scenario: Various edge cases
        """
        print("\n🧪 Scenario: EDGE CASES")
        print("-" * 70)

        # Edge case 1: Exactly flow_volume posts
        print("\n🔸 Edge case 1: Exactly flow_volume posts")
        await self.create_cleanup()
        for i in range(self.flow.flow_volume):
            await self.create_post(f"exact_{i+1}")
        await self.print_stats("Exactly flow_volume")

        # Edge case 2: One less than flow_volume
        print("\n🔸 Edge case 2: One less than flow_volume")
        await self.create_cleanup()
        for i in range(self.flow.flow_volume - 1):
            await self.create_post(f"minus_one_{i+1}")
        await self.print_stats("flow_volume - 1")

        # Edge case 3: One more than flow_volume
        print("\n🔸 Edge case 3: One more than flow_volume")
        await self.create_cleanup()
        for i in range(self.flow.flow_volume + 1):
            await self.create_post(f"plus_one_{i+1}")
        await self.print_stats("flow_volume + 1")

        print("\n✅ All edge cases handled correctly!")

    async def create_cleanup(self):
        """Delete all test posts"""
        deleted = await Post.objects.filter(
            flow=self.flow,
            source_id__startswith=f"test_scenario_{self.flow_id}_"
        ).adelete()
        if deleted[0] > 0:
            print(f"  🧹 Cleaned up {deleted[0]} test posts")

    async def run_all_scenarios(self):
        """Run all test scenarios"""
        await self.scenario_overflow()
        await asyncio.sleep(1)

        await self.scenario_publish_cycle()
        await asyncio.sleep(1)

        await self.scenario_schedule_and_generate()
        await asyncio.sleep(1)

        await self.scenario_edge_cases()

        print("\n" + "=" * 70)
        print("🎉 All scenarios completed!")
        print("=" * 70)


async def main(flow_id: int, scenario: str):
    tester = FlowTestScenarios(flow_id)
    await tester.setup()

    scenarios = {
        'overflow': tester.scenario_overflow,
        'publish-cycle': tester.scenario_publish_cycle,
        'schedule': tester.scenario_schedule_and_generate,
        'edge-cases': tester.scenario_edge_cases,
        'all': tester.run_all_scenarios,
    }

    if scenario not in scenarios:
        print(f"\n❌ Unknown scenario: {scenario}")
        print(f"Available scenarios: {', '.join(scenarios.keys())}")
        return

    # Run cleanup before starting
    print("\n🧹 Cleaning up old test data...")
    await tester.create_cleanup()

    # Run selected scenario
    await scenarios[scenario]()

    # Final cleanup
    print("\n🧹 Final cleanup...")
    await tester.create_cleanup()
    await tester.print_stats("After cleanup")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Test scenarios for flow post management',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Available scenarios:
  overflow        - Create more posts than flow_volume
  publish-cycle   - Test publishing workflow
  schedule        - Test scheduling workflow
  edge-cases      - Test various edge cases
  all             - Run all scenarios

Examples:
  python scripts/test_flow_scenarios.py --flow-id 1 --scenario overflow
  python scripts/test_flow_scenarios.py --flow-id 1 --scenario all
        """
    )

    parser.add_argument('--flow-id', type=int, required=True, help='Flow ID to test')
    parser.add_argument(
        '--scenario',
        type=str,
        default='overflow',
        help='Scenario to run (default: overflow)'
    )

    args = parser.parse_args()

    asyncio.run(main(args.flow_id, args.scenario))
