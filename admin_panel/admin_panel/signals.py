from datetime import timedelta

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Subscription, Tariff, User


@receiver(post_save, sender=User)
def create_trial_subscription(sender, instance, created, **kwargs):
    if created:
        free_tariff = Tariff.objects.filter(code=Tariff.FREE).first()
        if not free_tariff:
            return

        period = free_tariff.periods.filter(months=1).first()
        if not period:
            return

        Subscription.objects.create(
            user=instance,
            tariff_period=period,
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=free_tariff.trial_duration_days),
            is_trial=True,
            is_active=True,
        )
