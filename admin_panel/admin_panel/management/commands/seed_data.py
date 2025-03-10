from django.core.management.base import BaseCommand
from core.models import User, Channel, Flow, Post
from faker import Faker
import random
from django.utils import timezone

fake = Faker()

class Command(BaseCommand):
    help = "Заповнення бази тестовими даними"

    def handle(self, *args, **kwargs):
        # Створення користувачів
        for _ in range(10):
            User.objects.create(
                telegram_id=fake.random_int(min=100000000, max=999999999),
                username=fake.user_name(),
                subscription_status=fake.boolean(),
                subscription_end_date=fake.future_date(),
            )

        # Створення каналів
        users = User.objects.all()
        for user in users:
            Channel.objects.create(
                user=user,
                channel_name=fake.word(),
                channel_id=fake.random_int(min=100000000, max=999999999),
            )

        # Створення флоу
        channels = Channel.objects.all()
        for channel in channels:
            Flow.objects.create(
                channel=channel,
                name=fake.sentence(),
                source_type=random.choice(["Telegram", "Instagram", "Twitter", "Web"]),
                parameters={"param1": "value1", "param2": "value2"},
            )

        # Створення постів
        flows = Flow.objects.all()
        for flow in flows:
            Post.objects.create(
                flow=flow,
                content=fake.text(),
                source_url=fake.url(),
                status=random.choice(["draft", "published"]),
                scheduled_time=timezone.make_aware(fake.future_datetime()),
            )

        self.stdout.write(self.style.SUCCESS("Тестові дані успішно створені!"))