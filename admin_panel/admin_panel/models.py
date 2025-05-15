from datetime import timezone
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
        to_100 = "to_100", "До 100 знаків"
        to_300 = "to_300", "До 300 знаків"
        to_1000 = "to_1000", "До 1000 знаків"

    class GenerationFrequency(models.TextChoices):
        HOURLY = "hourly", "Кожну годину"
        TWELVEHOUR = "12h", "Раз на 12 год"
        DAILY = "daily", "Раз на день"

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

    next_generation_time = models.DateTimeField(null=True, blank=True, verbose_name="Наступна генерація")
    last_generated_at = models.DateTimeField(null=True, blank=True, verbose_name="Остання генерація")

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


class PostImage(models.Model):
    post = models.ForeignKey(
        'Post', 
        on_delete=models.CASCADE, 
        related_name='images',
        verbose_name="Пост"
    )
    image = models.ImageField(
        upload_to='posts/images/',
        verbose_name="Зображення",
        max_length=255
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name="Порядок сортування"
    )

    class Meta:
        verbose_name = "Зображення поста"
        verbose_name_plural = "Зображення постів"
        ordering = ['order']

    def __str__(self):
        return f"Зображення для поста {self.post.id}"

class Post(models.Model):
    DRAFT = 'draft'
    SCHEDULED = 'scheduled'
    PUBLISHED = 'published'
    
    STATUS_CHOICES = [
        (DRAFT, 'Чернетка'),
        (SCHEDULED, 'Заплановано'),
        (PUBLISHED, 'Опубліковано'),
    ]
    
    flow = models.ForeignKey(Flow, on_delete=models.CASCADE, related_name='posts', verbose_name="Флоу")
    content = models.TextField(verbose_name="Контент")
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=DRAFT,
        verbose_name="Статус"
    )
    source_id = models.CharField(
        max_length=255,
        unique=True,
        blank=True,
        null=True,
        verbose_name="Унікальний ID із джерела",
        help_text="Ідентифікатор посту в оригінальному джерелі (Telegram/Web)"
    )
    source_url = models.URLField(blank=True, null=True, verbose_name="Посилання на джерело")
    original_link = models.CharField(blank=True, null=True, verbose_name="Посилання на оригiнальний пост")
    publication_date = models.DateTimeField(blank=True, null=True, verbose_name="Дата публікації")
    scheduled_time = models.DateTimeField(null=True, blank=True, verbose_name="Запланований час")
    original_date = models.DateTimeField(blank=True, null=True, verbose_name="Дата оригiнальної публікації")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата створення")
    video = models.FileField(
        upload_to='posts/videos/',
        blank=True,
        null=True,
        verbose_name="Відео"
    )
    
    @property
    def media_type(self):
        if self.images.exists():
            return 'image'
        elif self.video:
            return 'video'
        return None
    
    @property
    def first_image_url(self):
        first_image = self.images.first()
        if first_image:
            return first_image.image.url
        return None

    @property
    def image_urls(self):
        return [img.image.url for img in self.images.all()]

    def save(self, *args, **kwargs):
        if self.status == self.PUBLISHED and not self.publication_date:
            self.publication_date = timezone.now()
        elif self.scheduled_time and not self.status == self.PUBLISHED:
            self.status = self.SCHEDULED
        super().save(*args, **kwargs)

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
    flow = models.OneToOneField(
        Flow,
        on_delete=models.CASCADE,
        related_name='ai_settings',
        verbose_name="Флоу",
        blank=True,
        null=True,
    )
    prompt = models.TextField(verbose_name="Промпт")
    style = models.CharField(max_length=100, verbose_name="Стиль")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата створення")

    def __str__(self):
        return f"Налаштування AI для {self.flow}"

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
