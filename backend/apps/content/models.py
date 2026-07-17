from django.db import models

from apps.content.constants import CHAT_TYPE_CHOICES, CHAT_TYPE_OPEN, FILE_TYPE_CHOICES


class Banner(models.Model):
    title = models.CharField("Заголовок", max_length=255)
    subtitle = models.TextField("Подзаголовок", blank=True, null=True)
    image_url = models.CharField("URL изображения", max_length=500)
    link_url = models.CharField("URL ссылки", max_length=500, blank=True, null=True)
    tags = models.JSONField(
        "Теги",
        default=list,
        blank=True,
        help_text='["новости", "акция"]',
    )
    is_active = models.BooleanField("Активен", default=True)
    sort_order = models.SmallIntegerField("Порядок", default=0)
    active_from = models.DateTimeField("Активен с", blank=True, null=True)
    active_until = models.DateTimeField("Активен до", blank=True, null=True)
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлён", auto_now=True)

    class Meta:
        verbose_name = "Баннер"
        verbose_name_plural = "Баннеры"
        db_table = "content_banner"
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.title


class MaterialCategory(models.Model):
    slug = models.SlugField("Slug", max_length=50, unique=True)
    name = models.CharField("Название", max_length=100)
    icon = models.CharField("Иконка", max_length=50, blank=True, null=True)
    sort_order = models.SmallIntegerField("Порядок", default=0)

    class Meta:
        verbose_name = "Категория материалов"
        verbose_name_plural = "Категории материалов"
        db_table = "content_material_category"
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name


class MaterialGroup(models.Model):
    category = models.ForeignKey(
        MaterialCategory,
        on_delete=models.CASCADE,
        related_name="groups",
        verbose_name="Категория",
    )
    title = models.CharField("Название", max_length=255)
    description = models.TextField("Описание", blank=True, null=True)
    file_type = models.CharField("Тип файла", max_length=20, choices=FILE_TYPE_CHOICES)
    file_count = models.PositiveIntegerField("Количество файлов", default=0)
    required_tariff = models.CharField(
        "Требуемый тариф", max_length=20, blank=True, null=True
    )
    sort_order = models.SmallIntegerField("Порядок", default=0)
    updated_at = models.DateTimeField("Обновлён", auto_now=True)

    class Meta:
        verbose_name = "Группа материалов"
        verbose_name_plural = "Группы материалов"
        db_table = "content_material_group"
        ordering = ["sort_order", "id"]

    def __str__(self):
        return f"{self.category.slug} · {self.title}"


class MaterialFile(models.Model):
    group = models.ForeignKey(
        MaterialGroup,
        on_delete=models.CASCADE,
        related_name="files",
        verbose_name="Группа",
    )
    title = models.CharField("Название", max_length=255)
    file_url = models.CharField("URL файла", max_length=500)
    file_size = models.PositiveIntegerField("Размер, байт", blank=True, null=True)
    format = models.CharField("Формат", max_length=20)
    sort_order = models.SmallIntegerField("Порядок", default=0)
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлён", auto_now=True)

    class Meta:
        verbose_name = "Файл материалов"
        verbose_name_plural = "Файлы материалов"
        db_table = "content_material_file"
        ordering = ["sort_order", "id"]
        indexes = [
            models.Index(fields=["group"], name="content_file_group_idx"),
        ]

    def __str__(self):
        return self.title


class TelegramChat(models.Model):
    title = models.CharField("Название", max_length=255)
    description = models.TextField("Описание", blank=True)
    chat_type = models.CharField(
        "Тип чата",
        max_length=20,
        choices=CHAT_TYPE_CHOICES,
        default=CHAT_TYPE_OPEN,
    )
    telegram_url = models.CharField("Ссылка Telegram", max_length=500)
    min_rank = models.CharField("Мин. ранг", max_length=50, blank=True, null=True)
    access_requirement = models.CharField(
        "Условие доступа", max_length=255, blank=True, null=True
    )
    is_active = models.BooleanField("Активен", default=True)
    sort_order = models.SmallIntegerField("Порядок", default=0)

    class Meta:
        verbose_name = "Telegram-чат"
        verbose_name_plural = "Telegram-чаты"
        db_table = "content_telegram_chat"
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.title
