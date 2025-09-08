from django.core.management.base import BaseCommand
import asyncio
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Generate test data for bot testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=5,
            help='Number of test users to create'
        )
        parser.add_argument(
            '--min-channels',
            type=int,
            default=1,
            help='Minimum channels per user'
        )
        parser.add_argument(
            '--max-channels',
            type=int,
            default=3,
            help='Maximum channels per user'
        )
        parser.add_argument(
            '--min-flows',
            type=int,
            default=1,
            help='Minimum flows per channel'
        )
        parser.add_argument(
            '--max-flows',
            type=int,
            default=2,
            help='Maximum flows per channel'
        )
        parser.add_argument(
            '--min-sources',
            type=int,
            default=2,
            help='Minimum sources per flow'
        )
        parser.add_argument(
            '--max-sources',
            type=int,
            default=5,
            help='Maximum sources per flow'
        )
        parser.add_argument(
            '--cleanup',
            action='store_true',
            help='Cleanup existing test data before generation'
        )

    def handle(self, *args, **options):
        from admin_panel.testing.data_generator import generate_test_data, cleanup_test_data

        async def run_generation():
            if options['cleanup']:
                self.stdout.write("Cleaning up existing test data...")
                deleted = await cleanup_test_data()
                self.stdout.write(f"Cleaned up {deleted} test users")

            self.stdout.write("Generating test data...")

            result = await generate_test_data(
                user_count=options['users'],
                min_channels=options['min_channels'],
                max_channels=options['max_channels'],
                min_flows=options['min_flows'],
                max_flows=options['max_flows'],
                min_sources=options['min_sources'],
                max_sources=options['max_sources']
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully generated test data:\n"
                    f"• Users: {len(result['users'])}\n"
                    f"• Channels: {len(result['channels'])}\n"
                    f"• Flows: {len(result['flows'])}\n"
                    f"• Sources: {result['sources']}"
                )
            )

        asyncio.run(run_generation())