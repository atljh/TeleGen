import logging

from django.core.management.base import BaseCommand
from django.db import transaction

from admin_panel.models import Tariff, TariffPeriod

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Seed tariffs and tariff periods"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing tariffs before seeding",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            self.stdout.write("Clearing existing tariffs...")
            deleted_periods = TariffPeriod.objects.all().delete()[0]
            deleted_tariffs = Tariff.objects.all().delete()[0]
            self.stdout.write(
                self.style.WARNING(
                    f"Deleted {deleted_tariffs} tariffs and {deleted_periods} tariff periods"
                )
            )

        self.stdout.write("Seeding tariffs...")

        with transaction.atomic():
            # Welcome (Free) Tariff
            welcome_tariff, created = Tariff.objects.get_or_create(
                code="free",
                defaults={
                    "name": "Welcome",
                    "description": "Безкоштовний тестовий період для ознайомлення з сервісом",
                    "channels_available": 1,
                    "sources_available": 2,
                    "generations_available": 300,
                    "platforms": Tariff.PLATFORM_BOTH,
                    "is_active": True,
                    "trial_duration_days": 10,
                },
            )
            if created:
                self.stdout.write(f"✓ Created tariff: {welcome_tariff.name}")
            else:
                self.stdout.write(f"○ Tariff already exists: {welcome_tariff.name}")

            # Create periods for Welcome tariff (only trial, so no paid periods)
            # The trial_duration_days handles the free period

            # Basic Tariff
            basic_tariff, created = Tariff.objects.get_or_create(
                code="basic",
                defaults={
                    "name": "Basic",
                    "description": "Базовий тариф для початківців",
                    "channels_available": 1,
                    "sources_available": 5,
                    "generations_available": 1000,
                    "platforms": Tariff.PLATFORM_TG,
                    "is_active": True,
                    "trial_duration_days": 0,
                },
            )
            if created:
                self.stdout.write(f"✓ Created tariff: {basic_tariff.name}")
            else:
                self.stdout.write(f"○ Tariff already exists: {basic_tariff.name}")

            # Create periods for Basic tariff
            basic_periods = [
                {"months": 1, "price": 299.00},
                {"months": 6, "price": 1499.00},
                {"months": 9, "price": 1999.00},
                {"months": 12, "price": 2399.00},
            ]

            for period_data in basic_periods:
                period, created = TariffPeriod.objects.get_or_create(
                    tariff=basic_tariff,
                    months=period_data["months"],
                    defaults={"price": period_data["price"]},
                )
                if created:
                    self.stdout.write(
                        f"  ✓ Created period: {period.get_months_display()} - {period.price}₴"
                    )

            # Pro Tariff
            pro_tariff, created = Tariff.objects.get_or_create(
                code="pro",
                defaults={
                    "name": "Pro",
                    "description": "Професійний тариф для досвідчених користувачів",
                    "channels_available": 3,
                    "sources_available": 5,
                    "generations_available": 3000,
                    "platforms": Tariff.PLATFORM_BOTH,
                    "is_active": True,
                    "trial_duration_days": 0,
                },
            )
            if created:
                self.stdout.write(f"✓ Created tariff: {pro_tariff.name}")
            else:
                self.stdout.write(f"○ Tariff already exists: {pro_tariff.name}")

            # Create periods for Pro tariff
            pro_periods = [
                {"months": 1, "price": 599.00},
                {"months": 6, "price": 2999.00},
                {"months": 9, "price": 3999.00},
                {"months": 12, "price": 4799.00},
            ]

            for period_data in pro_periods:
                period, created = TariffPeriod.objects.get_or_create(
                    tariff=pro_tariff,
                    months=period_data["months"],
                    defaults={"price": period_data["price"]},
                )
                if created:
                    self.stdout.write(
                        f"  ✓ Created period: {period.get_months_display()} - {period.price}₴"
                    )

        self.stdout.write(
            self.style.SUCCESS(
                "\n✅ Successfully seeded tariffs!\n\n"
                "Summary:\n"
                f"• Welcome (Free): 1 канал, 2 джерела, 300 генерацій, 10 днів тестового періоду\n"
                f"• Basic: 1 канал, 5 джерел (TG), 1000 генерацій/міс\n"
                f"• Pro: 3 канали, 5 джерел (TG + Web), 3000 генерацій/міс"
            )
        )
