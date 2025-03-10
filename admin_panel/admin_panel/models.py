from django.db import models

class User(models.Model):
    telegram_id = models.BigIntegerField(unique=True, verbose_name="Telegram ID")
    username = models.CharField(max_length=100, null=True, blank=True, verbose_name="Ім'я користувача")
    subscription_status = models.BooleanField(default=False, verbose_name="Статус підписки")
    subscription_end_date = models.DateTimeField(null=True, blank=True, verbose_name="Дата закінчення підписки")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата створення")

    def __str__(self):
        return f"User {self.telegram_id}"

    class Meta:
        verbose_name = "Користувач"
        verbose_name_plural = "Користувачі"


class Channel(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Користувач")
    channel_name = models.CharField(max_length=100, verbose_name="Назва каналу")
    channel_id = models.BigIntegerField(unique=True, verbose_name="ID каналу")
    added_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата додавання")

    def __str__(self):
        return f"Channel {self.channel_name}"

    class Meta:
        verbose_name = "Канал"
        verbose_name_plural = "Канали"


class Flow(models.Model):
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, verbose_name="Канал")
    name = models.CharField(max_length=100, verbose_name="Назва флоу")
    source_type = models.CharField(max_length=50, verbose_name="Тип джерела")  # Telegram, Instagram, Twitter, Web
    parameters = models.JSONField(verbose_name="Параметри")  # Налаштування флоу
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата створення")

    def __str__(self):
        return f"Flow {self.name}"

    class Meta:
        verbose_name = "Флоу"
        verbose_name_plural = "Флоу"


class Post(models.Model):
    flow = models.ForeignKey(Flow, on_delete=models.CASCADE, verbose_name="Флоу")
    content = models.TextField(verbose_name="Вміст поста")
    source_url = models.URLField(null=True, blank=True, verbose_name="Посилання на джерело")
    status = models.CharField(max_length=50, default="draft", verbose_name="Статус")  # draft, published
    scheduled_time = models.DateTimeField(null=True, blank=True, verbose_name="Запланований час")
    published_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата публікації")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата створення")

    def __str__(self):
        return f"Post {self.id}"

    class Meta:
        verbose_name = "Пост"
        verbose_name_plural = "Пости"