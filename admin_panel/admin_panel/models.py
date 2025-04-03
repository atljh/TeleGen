from django.db import models

class User(models.Model):
    telegram_id = models.BigIntegerField(unique=True, verbose_name="Telegram ID")
    username = models.CharField(max_length=100, null=True, blank=True, verbose_name="Telegram username")
    first_name = models.CharField(max_length=100, null=True, blank=True, verbose_name="Ім'я")
    last_name = models.CharField(max_length=100, null=True, blank=True, verbose_name="Прізвище")
    subscription_status = models.BooleanField(default=False, verbose_name="Статус підписки")
    subscription_end_date = models.DateTimeField(null=True, blank=True, verbose_name="Дата закінчення підписки")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата створення")
    subscription_type = models.CharField(max_length=50, null=True, blank=True, verbose_name="Тип підписки")
    payment_method = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return f"{self.username} (Telegram ID: {self.telegram_id})"

    class Meta:
        verbose_name = "Користувач"
        verbose_name_plural = "Користувачі"


class Channel(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='channels', verbose_name="Користувач")
    channel_id = models.CharField(max_length=100, unique=True, verbose_name="ID каналу")
    name = models.CharField(max_length=255, verbose_name="Назва каналу")
    description = models.TextField(blank=True, null=True, verbose_name="Опис каналу")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата створення")
    is_active = models.BooleanField(default=True, verbose_name="Активний")

    def __str__(self):
        return f"{self.name} (ID: {self.channel_id})"

    class Meta:
        verbose_name = "Канал"
        verbose_name_plural = "Канали"


class Flow(models.Model):
    class ContentLength(models.TextChoices):
        SHORT = "short", "Короткий (до 300 знаків)"
        MEDIUM = "medium", "Середній (300-1000 знаків)"
        LONG = "long", "Довгий (понад 1000 знаків)"

    class GenerationFrequency(models.TextChoices):
        HOURLY = "hourly", "Кожну годину"
        DAILY = "daily", "Раз на день"
        WEEKLY = "weekly", "Раз на тиждень"
        CUSTOM = "custom", "Користувацький графік"

    channel = models.OneToOneField(
        Channel,
        on_delete=models.CASCADE,
        primary_key=False,
        unique=True
    )
    name = models.CharField(max_length=255, verbose_name="Назва флоу")
    theme = models.CharField(max_length=100, verbose_name="Тематика")
    sources = models.JSONField(
        default=list,
        verbose_name="Джерела контенту"
    )  # Список: [{"type": "telegram", "link": "..."}, ...]
    content_length = models.CharField(
        max_length=50,
        choices=ContentLength.choices,
        verbose_name="Обсяг тексту"
    )
    use_emojis = models.BooleanField(default=False, verbose_name="Використання емодзі")
    use_premium_emojis = models.BooleanField(default=False, verbose_name="Преміум емодзі")
    title_highlight = models.BooleanField(default=False, verbose_name="Виділення заголовків")
    cta = models.BooleanField(default=False, verbose_name="Заклик до дії (CTA)")
    frequency = models.CharField(
        max_length=50,
        choices=GenerationFrequency.choices,
        verbose_name="Частота генерації"
    )
    signature = models.TextField(
        null=True,
        blank=True,
        verbose_name="Підпис до постів"
    )
    flow_volume = models.PositiveSmallIntegerField(
        default=5,
        verbose_name="Кількість постів у флоу"
    )
    ad_time = models.CharField(
        max_length=5,
        null=True,
        blank=True,
        verbose_name="Час для рекламних топів (HH:MM)"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата створення")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата оновлення")

    def __str__(self):
        return f"{self.name} ({self.theme})"

    class Meta:
        verbose_name = "Флоу"
        verbose_name_plural = "Флоу"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["channel", "created_at"]),
            models.Index(fields=["name"]),
        ]


class Post(models.Model):
    flow = models.ForeignKey(Flow, on_delete=models.CASCADE, related_name='posts', verbose_name="Флоу")
    content = models.TextField(verbose_name="Контент")
    source_url = models.URLField(blank=True, null=True, verbose_name="Посилання на джерело")
    publication_date = models.DateTimeField(blank=True, null=True, verbose_name="Дата публікації")
    is_published = models.BooleanField(default=False, verbose_name="Опубліковано")
    is_draft = models.BooleanField(default=False, verbose_name="Чернетка")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата створення")
    image = models.ImageField(
        upload_to='posts/images/',
        blank=True,
        null=True,
        verbose_name="Зображення"
    )


    def __str__(self):
        return f"Пост від {self.created_at.strftime('%Y-%m-%d %H:%M')}"

    class Meta:
        verbose_name = "Пост"
        verbose_name_plural = "Пости"


class Draft(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='drafts', verbose_name="Користувач")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='drafts', verbose_name="Пост")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата створення")

    def __str__(self):
        return f"Чернетка для {self.user.username}"

    class Meta:
        verbose_name = "Чернетка"
        verbose_name_plural = "Чернетки"


class Subscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions', verbose_name="Користувач")
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='subscriptions', verbose_name="Канал")
    subscription_type = models.CharField(max_length=50, verbose_name="Тип підписки")
    start_date = models.DateTimeField(auto_now_add=True, verbose_name="Дата початку")
    end_date = models.DateTimeField(verbose_name="Дата закінчення")
    is_active = models.BooleanField(default=True, verbose_name="Активна")

    def __str__(self):
        return f"Підписка {self.subscription_type} для {self.user.username}"

    class Meta:
        verbose_name = "Підписка"
        verbose_name_plural = "Підписки"


class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments', verbose_name="Користувач")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Сума")
    payment_method = models.CharField(max_length=50, verbose_name="Метод оплати")
    payment_date = models.DateTimeField(auto_now_add=True, verbose_name="Дата оплати")
    is_successful = models.BooleanField(default=False, verbose_name="Успішний")

    def __str__(self):
        return f"Платіж {self.amount} від {self.user.username}"

    class Meta:
        verbose_name = "Платіж"
        verbose_name_plural = "Платежі"


class AISettings(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_settings', verbose_name="Користувач")
    prompt = models.TextField(verbose_name="Промпт")
    style = models.CharField(max_length=100, verbose_name="Стиль")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата створення")

    def __str__(self):
        return f"Налаштування AI для {self.user.username}"

    class Meta:
        verbose_name = "Налаштування AI"
        verbose_name_plural = "Налаштування AI"


class Statistics(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='statistics', verbose_name="Користувач")
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='statistics', verbose_name="Канал")
    total_posts = models.IntegerField(default=0, verbose_name="Всього постів")
    total_views = models.IntegerField(default=0, verbose_name="Всього переглядів")
    total_likes = models.IntegerField(default=0, verbose_name="Всього лайків")
    last_updated = models.DateTimeField(auto_now=True, verbose_name="Останнє оновлення")

    def __str__(self):
        return f"Статистика для {self.user.username}"

    class Meta:
        verbose_name = "Статистика"
        verbose_name_plural = "Статистика"
