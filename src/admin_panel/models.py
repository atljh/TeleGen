from typing import ClassVar

from dateutil.relativedelta import relativedelta
from django.db import models
from django.utils import timezone


def default_generation_reset_at():
    return timezone.now() + relativedelta(months=1)


class User(models.Model):
    telegram_id = models.BigIntegerField(unique=True, verbose_name="Telegram ID")
    username = models.CharField(
        max_length=100, blank=True, verbose_name="Telegram username"
    )
    first_name = models.CharField(max_length=100, blank=True, verbose_name="Ім'я")
    last_name = models.CharField(max_length=100, blank=True, verbose_name="Прізвище")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата створення")

    generated_posts_count = models.PositiveIntegerField(
        default=0, verbose_name="Кількість генерацій"
    )
    generation_reset_at = models.DateTimeField(
        default=default_generation_reset_at,
        null=True,
        blank=True,
        verbose_name="Час наступного скидання генерацій",
    )

    class Meta:
        verbose_name = "Користувач"
        verbose_name_plural = "Користувачі"

    def __str__(self):
        return f"{self.username} (Telegram ID: {self.telegram_id})"


class Channel(models.Model):
    TIMEZONE_CHOICES: ClassVar[list[tuple[str, str]]] = [
        ("Europe/Kiev", "🇺🇦 Київ (UTC+2)"),
        ("Europe/London", "🇪🇺 Лондон (UTC+0)"),
        ("America/New_York", "🇺🇸 Нью-Йорк (UTC-4)"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="channels",
        verbose_name="Користувач",
    )
    channel_id = models.CharField(max_length=100, unique=True, verbose_name="ID каналу")
    name = models.CharField(max_length=255, verbose_name="Назва каналу")
    description = models.TextField(blank=True, verbose_name="Опис каналу")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата створення")
    is_active = models.BooleanField(default=True, verbose_name="Активний")
    notifications = models.BooleanField(default=False, verbose_name="Сповiщення")
    timezone = models.CharField(
        max_length=50,
        choices=TIMEZONE_CHOICES,
        default="Europe/Kiev",
        verbose_name="Часовий пояс",
    )

    class Meta:
        verbose_name = "Канал"
        verbose_name_plural = "Канали"

    def __str__(self):
        return f"{self.name} (ID: {self.channel_id})"


class Flow(models.Model):
    class ContentLength(models.TextChoices):
        to_100 = "to_100", "До 100 знаків"
        to_300 = "to_300", "До 300 знаків"
        to_1000 = "to_1000", "До 1000 знаків"

    class GenerationFrequency(models.TextChoices):
        HOURLY = "hourly", "Кожну годину"
        TWELVEHOUR = "12h", "Раз на 12 год"
        DAILY = "daily", "Раз на день"

    channel = models.OneToOneField(
        Channel, on_delete=models.CASCADE, primary_key=False, unique=True
    )
    name = models.CharField(max_length=255, verbose_name="Назва флоу")
    theme = models.CharField(max_length=100, verbose_name="Тематика")
    sources = models.JSONField(
        default=list, verbose_name="Джерела контенту"
    )  # Список: [{"type": "telegram", "link": "..."}, ...]
    content_length = models.CharField(
        max_length=50, choices=ContentLength.choices, verbose_name="Обсяг тексту"
    )
    use_emojis = models.BooleanField(default=False, verbose_name="Використання емодзі")
    use_premium_emojis = models.BooleanField(
        default=False, verbose_name="Преміум емодзі"
    )
    title_highlight = models.BooleanField(
        default=False, verbose_name="Виділення заголовків"
    )
    cta = models.BooleanField(default=False, verbose_name="Заклик до дії (CTA)")
    frequency = models.CharField(
        max_length=50,
        choices=GenerationFrequency.choices,
        verbose_name="Частота генерації",
    )
    signature = models.TextField(blank=True, verbose_name="Підпис до постів")
    flow_volume = models.PositiveSmallIntegerField(
        default=5, verbose_name="Кількість постів у флоу"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата створення")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата оновлення")

    next_generation_time = models.DateTimeField(
        null=True, blank=True, verbose_name="Наступна генерація"
    )
    last_generated_at = models.DateTimeField(
        null=True, blank=True, verbose_name="Остання генерація"
    )

    class Meta:
        verbose_name = "Флоу"
        verbose_name_plural = "Флоу"
        ordering: ClassVar[list[str]] = ["-created_at"]
        indexes: ClassVar[list[models.Index]] = [
            models.Index(fields=["channel", "created_at"]),
            models.Index(fields=["name"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.theme})"


class PostImage(models.Model):
    post = models.ForeignKey(
        "Post", on_delete=models.CASCADE, related_name="images", verbose_name="Пост"
    )
    image = models.ImageField(
        upload_to="posts/images/", verbose_name="Зображення", max_length=255
    )
    url = models.URLField(verbose_name="Посилання на зображення", blank=True)
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок сортування")

    class Meta:
        verbose_name = "Зображення поста"
        verbose_name_plural = "Зображення постів"
        ordering: ClassVar[list[str]] = ["order"]

    def __str__(self):
        return f"Зображення для поста {self.post.id}"

    @property
    def source_url(self):
        if self.url:
            return self.image
        return self.image


class PostVideo(models.Model):
    post = models.ForeignKey(
        "Post", on_delete=models.CASCADE, related_name="videos", verbose_name="Пост"
    )
    video = models.FileField(
        upload_to="posts/videos/", verbose_name="Вiдео", max_length=255
    )
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок сортування")

    class Meta:
        verbose_name = "Вiдео поста"
        verbose_name_plural = "Вiдео постів"
        ordering: ClassVar[list[str]] = ["order"]

    def __str__(self):
        return f"Вiдео для поста {self.post.id}"


class Post(models.Model):
    DRAFT: ClassVar[str] = "draft"
    SCHEDULED: ClassVar[str] = "scheduled"
    PUBLISHED: ClassVar[str] = "published"

    STATUS_CHOICES: ClassVar[list[tuple[str, str]]] = [
        (DRAFT, "Чернетка"),
        (SCHEDULED, "Заплановано"),
        (PUBLISHED, "Опубліковано"),
    ]

    flow = models.ForeignKey(
        Flow, on_delete=models.CASCADE, related_name="posts", verbose_name="Флоу"
    )
    content = models.TextField(verbose_name="Контент")
    original_content = models.TextField(
        verbose_name="Оригiнальний текст", blank=True, default=""
    )
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default=DRAFT, verbose_name="Статус"
    )
    source_id = models.CharField(
        max_length=255,
        unique=True,
        blank=True,
        null=True,
        verbose_name="Унікальний ID із джерела",
        help_text="Ідентифікатор посту в оригінальному джерелі (Telegram/Web)",
    )
    source_url = models.URLField(blank=True, verbose_name="Посилання на джерело")
    original_link = models.CharField(
        blank=True, max_length=500, verbose_name="Посилання на оригiнальний пост"
    )
    publication_date = models.DateTimeField(
        blank=True, null=True, verbose_name="Дата публікації"
    )
    scheduled_time = models.DateTimeField(
        null=True, blank=True, verbose_name="Запланований час"
    )
    original_date = models.DateTimeField(
        blank=True, null=True, verbose_name="Дата оригiнальної публікації"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата створення")

    class Meta:
        verbose_name = "Пост"
        verbose_name_plural = "Пости"
        constraints: ClassVar[list[models.UniqueConstraint]] = [
            models.UniqueConstraint(
                fields=["source_id"],
                name="unique_source_id",
                condition=models.Q(source_id__isnull=False),
            )
        ]

    def __str__(self):
        return f"Пост від {self.created_at.strftime('%Y-%m-%d %H:%M')}"

    @property
    def media_type(self):
        if self.images.exists():
            return "image"
        elif self.videos.exists():
            return "video"
        return None

    @property
    def images_list(self):
        return list(self.images.all())


class Draft(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="drafts", verbose_name="Користувач"
    )
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name="drafts", verbose_name="Пост"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата створення")

    class Meta:
        verbose_name = "Чернетка"
        verbose_name_plural = "Чернетки"

    def __str__(self):
        return f"Чернетка для {self.user.username}"


class Payment(models.Model):
    class PaymentMethod(models.TextChoices):
        CARD = "card", "Банківська карта"
        CRYPTO = "crypto", "Криптовалюта"

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="payments",
        verbose_name="Користувач",
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Сума")
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        verbose_name="Метод оплати",
    )
    payment_date = models.DateTimeField(auto_now_add=True, verbose_name="Дата оплати")
    is_successful = models.BooleanField(default=False, verbose_name="Успішний")
    subscription = models.ForeignKey(
        "Subscription",
        on_delete=models.CASCADE,
        related_name="payments",
        verbose_name="Підписка",
        null=True,
        blank=True,
    )

    tariff_period = models.ForeignKey(
        "TariffPeriod",
        on_delete=models.PROTECT,
        related_name="payments",
        verbose_name="Тарифний період",
        null=True,
        blank=True,
    )
    subscription = models.ForeignKey(
        "Subscription",
        on_delete=models.CASCADE,
        related_name="payments",
        verbose_name="Підписка",
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата створення")

    order_id = models.CharField(max_length=100, unique=True)
    external_id = models.CharField(max_length=100, blank=True, null=True, unique=True)
    pay_url = models.URLField(blank=True)

    class Meta:
        verbose_name = "Платіж"
        verbose_name_plural = "Платежі"

    def __str__(self):
        return f"{self.get_payment_method_display()} – {self.amount}₴ ({'✅' if self.is_successful else '❌'})"


class AISettings(models.Model):
    flow = models.OneToOneField(
        Flow,
        on_delete=models.CASCADE,
        related_name="ai_settings",
        verbose_name="Флоу",
        blank=True,
        null=True,
    )
    prompt = models.TextField(verbose_name="Промпт")
    role = models.CharField(max_length=255, verbose_name="Роль", blank=True)
    role_content = models.TextField(verbose_name="Текст роли", blank=True)
    style = models.CharField(max_length=100, verbose_name="Стиль", blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата створення")

    class Meta:
        verbose_name = "Налаштування AI"
        verbose_name_plural = "Налаштування AI"

    def __str__(self):
        return f"Налаштування AI для {self.flow}"


class Statistics(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="statistics",
        verbose_name="Користувач",
    )
    channel = models.ForeignKey(
        Channel,
        on_delete=models.CASCADE,
        related_name="statistics",
        verbose_name="Канал",
    )
    total_posts = models.IntegerField(default=0, verbose_name="Всього постів")
    total_views = models.IntegerField(default=0, verbose_name="Всього переглядів")
    total_likes = models.IntegerField(default=0, verbose_name="Всього лайків")
    last_updated = models.DateTimeField(auto_now=True, verbose_name="Останнє оновлення")

    class Meta:
        verbose_name = "Статистика"
        verbose_name_plural = "Статистика"

    def __str__(self):
        return f"Статистика для {self.user.username}"


class Tariff(models.Model):
    FREE = "free"
    BASIC = "basic"
    PRO = "pro"

    TARIFF_CHOICES: ClassVar[list[tuple[str, str]]] = [
        (FREE, "Безкоштовний"),
        (BASIC, "Базовий"),
        (PRO, "Професійний"),
    ]

    PLATFORM_TG = "tg"
    PLATFORM_WEB = "web"
    PLATFORM_BOTH = "both"

    PLATFORM_CHOICES: ClassVar[list[tuple[str, str]]] = [
        (PLATFORM_TG, "Telegram"),
        (PLATFORM_WEB, "Web"),
        (PLATFORM_BOTH, "Telegram + Web"),
    ]

    code = models.CharField(
        max_length=50, choices=TARIFF_CHOICES, unique=True, verbose_name="Код тарифу"
    )
    name = models.CharField(max_length=100, verbose_name="Назва")
    description = models.TextField(blank=True, verbose_name="Опис")

    level = models.PositiveSmallIntegerField(
        default=1, help_text="Рівень тарифу (1 - безкоштовний, 2 - базовий, 3 - профі)"
    )

    channels_available = models.PositiveSmallIntegerField(
        default=0, verbose_name="Доступно каналів"
    )
    sources_available = models.PositiveSmallIntegerField(
        default=0, verbose_name="Доступно джерел"
    )
    generations_available = models.PositiveSmallIntegerField(
        default=0, verbose_name="Достпуно генерацій"
    )

    platforms = models.CharField(
        max_length=10,
        choices=PLATFORM_CHOICES,
        default=PLATFORM_TG,
        verbose_name="Платформи",
    )

    is_active = models.BooleanField(default=True, verbose_name="Активний")

    trial_duration_days = models.PositiveSmallIntegerField(
        default=0, verbose_name="Тривалість тестового періоду (днів)"
    )

    class Meta:
        verbose_name = "Тариф"
        verbose_name_plural = "Тарифи"
        ordering: ClassVar[list[str]] = ["level"]

    def __str__(self):
        return f"{self.get_name_display()} ({self.get_code_display()})"

    def get_name_display(self):
        return self.name

    def get_code_display(self):
        return self.code


class TariffPeriod(models.Model):
    PERIOD_CHOICES: ClassVar[list[tuple[int, str]]] = [
        (1, "1 місяць"),
        (6, "6 місяців"),
        (9, "9 місяців"),
        (12, "1 рік"),
    ]

    tariff = models.ForeignKey(
        Tariff, on_delete=models.CASCADE, related_name="periods", verbose_name="Тариф"
    )
    months = models.PositiveSmallIntegerField(
        choices=PERIOD_CHOICES, verbose_name="Термін підписки"
    )
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Ціна")
    promo_code = models.CharField(max_length=50, blank=True, verbose_name="Промокод")
    discount_percent = models.PositiveSmallIntegerField(
        default=0, verbose_name="Знижка (%)"
    )

    class Meta:
        verbose_name = "Термін тарифу"
        verbose_name_plural = "Терміни тарифів"
        unique_together = ("tariff", "months")

    def __str__(self):
        return f"{self.tariff} – {self.get_months_display()} ({self.price}₴)"


class Subscription(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="subscriptions",
        verbose_name="Користувач",
    )
    tariff_period = models.ForeignKey(
        TariffPeriod,
        on_delete=models.PROTECT,
        related_name="subscriptions",
        verbose_name="Тариф + період",
    )
    start_date = models.DateTimeField(auto_now_add=True, verbose_name="Дата початку")
    end_date = models.DateTimeField(verbose_name="Дата закінчення")
    is_active = models.BooleanField(default=True, verbose_name="Активна")

    class Meta:
        verbose_name = "Підписка"
        verbose_name_plural = "Підписки"

    def __str__(self):
        return f"{self.user.username} – {self.tariff_period}"
