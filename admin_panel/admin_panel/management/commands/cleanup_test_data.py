from django.core.management.base import BaseCommand
import asyncio

class Command(BaseCommand):
    help = 'Cleanup test data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all-users',
            action='store_true',
            help='Cleanup all test users (not just by prefix)'
        )

    def handle(self, *args, **options):
        from admin_panel.testing.data_generator import cleanup_test_data

        async def run_cleanup():
            if options['all_users']:
                from django.contrib.auth import get_user_model
                User = get_user_model()

                users_to_delete = await User.objects.filter(is_superuser=False).acount()
                await User.objects.filter(is_superuser=False).adelete()

                self.stdout.write(
                    self.style.SUCCESS(f"Cleaned up {users_to_delete} users")
                )
            else:
                deleted = await cleanup_test_data()
                self.stdout.write(
                    self.style.SUCCESS(f"Cleaned up {deleted} test users")
                )

        asyncio.run(run_cleanup())