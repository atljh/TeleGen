import random

from django.core.management.base import BaseCommand
from django.utils import timezone
from faker import Faker

from admin_panel.admin_panel.models import (
    AISettings,
    Channel,
    Draft,
    Flow,
    Payment,
    Post,
    Statistics,
    Subscription,
    User,
)

fake = Faker()


class Command(BaseCommand):
    help = "Заповнення бази тестовими даними"

    def handle(self, *args, **kwargs):
        for _ in range(10):
            User.objects.create(
                telegram_id=fake.random_int(min=100000000, max=999999999),
                username=fake.user_name(),
                subscription_type=random.choice(["Basic", "Premium", "Pro"]),
                subscription_end_date=fake.future_date(),
                payment_method=random.choice(["Credit Card", "Stars", "Crypto"]),
            )

        users = User.objects.all()

        for user in users:
            Channel.objects.create(
                user=user,
                channel_id=fake.random_int(min=100000000, max=999999999),
                name=fake.word(),
                description=fake.sentence(),
                is_active=fake.boolean(),
            )

        channels = Channel.objects.all()

        for channel in channels:
            Flow.objects.create(
                channel=channel,
                name=fake.sentence(),
                theme=random.choice(["Technology", "Health", "Finance", "Lifestyle"]),
                source=random.choice(["Telegram", "Instagram", "Twitter", "Web"]),
                content_length=random.choice(["Short", "Medium", "Long"]),
                use_emojis=fake.boolean(),
                use_premium_emojis=fake.boolean(),
                cta=fake.boolean(),
                frequency=random.choice(["Daily", "Weekly", "Monthly"]),
            )

        flows = Flow.objects.all()

        for flow in flows:
            Post.objects.create(
                flow=flow,
                content=fake.text(),
                source_url=fake.url(),
                publication_date=timezone.make_aware(fake.future_datetime()),
                is_published=fake.boolean(),
                is_draft=fake.boolean(),
            )

        posts = Post.objects.all()

        # Створення чернеток
        for post in posts:
            if post.is_draft:
                Draft.objects.create(
                    user=post.flow.channel.user,
                    post=post,
                )

        # Створення підписок
        for user in users:
            channel = random.choice(channels)
            Subscription.objects.create(
                user=user,
                channel=channel,
                subscription_type=random.choice(["Basic", "Premium", "Pro"]),
                start_date=timezone.now(),
                end_date=timezone.make_aware(fake.future_datetime()),
                is_active=fake.boolean(),
            )

        for user in users:
            Payment.objects.create(
                user=user,
                amount=fake.random_int(min=10, max=1000),
                payment_method=random.choice(["Credit Card", "Stars", "Crypto"]),
                is_successful=fake.boolean(),
            )

        for user in users:
            AISettings.objects.create(
                user=user,
                prompt=fake.sentence(),
                style=random.choice(["Formal", "Casual", "Technical", "Creative"]),
            )

        for channel in channels:
            Statistics.objects.create(
                user=channel.user,
                channel=channel,
                total_posts=fake.random_int(min=0, max=100),
                total_views=fake.random_int(min=0, max=1000),
                total_likes=fake.random_int(min=0, max=500),
            )
        self.stdout.write(self.style.SUCCESS("Тестові дані успішно створені!"))
