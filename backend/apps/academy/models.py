from django.conf import settings
from django.db import models

from apps.academy.constants import (
    LESSON_TYPE_CHOICES,
    LESSON_TYPE_VIDEO,
    PROGRESS_STATUS_CHOICES,
    RESOURCE_TYPE_CHOICES,
    STATUS_NOT_STARTED,
)


class Program(models.Model):
    slug = models.CharField(
        "Код в ссылке (slug)",
        max_length=100,
        unique=True,
        help_text="Латиницей без пробелов, например gpt-new. Используется в адресе /courses/gpt-new. Обычно заполняется сам из названия.",
    )
    title = models.CharField(
        "Название",
        max_length=255,
        help_text="Как программа называется в кабинете, например «GPT - NEW».",
    )
    description = models.TextField(
        "Описание",
        blank=True,
        help_text="Короткий текст под названием на карточке и в карточке курса.",
    )
    module_count = models.PositiveSmallIntegerField("Число модулей", default=0)
    lesson_count = models.PositiveSmallIntegerField("Число уроков", default=0)
    icon = models.CharField(
        "Иконка",
        max_length=50,
        blank=True,
        null=True,
        help_text="Пока можно оставить пустым — в кабинете подставится стандартная иконка.",
    )
    tags = models.JSONField(
        "Теги",
        default=list,
        blank=True,
        help_text='Список меток в формате JSON. Пример: ["HIT"] или ["Новинка", "Хит"]. На главной показывается первый тег как бейдж.',
    )
    required_tariff = models.CharField(
        "Минимальный тариф",
        max_length=20,
        blank=True,
        null=True,
        help_text="Код тарифа для доступа: rise, rise-pro или rise-pro-max. Пусто — без ограничения по тарифу.",
    )
    required_product = models.ForeignKey(
        "commerce.Product",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="academy_programs",
        verbose_name="Нужный продукт",
        help_text="Опционально: если доступ даётся только после покупки конкретного продукта.",
    )
    is_published = models.BooleanField(
        "Опубликована",
        default=False,
        help_text="Включите, когда программа готова. Неопубликованная в кабинете не видна.",
    )
    sort_order = models.SmallIntegerField(
        "Порядок",
        default=0,
        help_text="Чем меньше число, тем выше в списке (0, 1, 2…).",
    )
    created_at = models.DateTimeField("Создана", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлена", auto_now=True)

    class Meta:
        verbose_name = "Программа"
        verbose_name_plural = "Программы"
        db_table = "academy_program"
        ordering = ["sort_order", "title"]

    def __str__(self):
        return self.title


class Module(models.Model):
    program = models.ForeignKey(
        Program,
        on_delete=models.CASCADE,
        related_name="modules",
        verbose_name="Программа",
    )
    sort_order = models.SmallIntegerField(
        "Порядок",
        help_text="Порядок модуля внутри программы: 0, 1, 2…",
    )
    title = models.CharField("Название модуля", max_length=255)
    description = models.TextField("Описание модуля", blank=True, null=True)
    is_intro = models.BooleanField(
        "Вводный модуль",
        default=False,
        help_text="Отметьте, если это короткое введение в начале курса.",
    )
    lesson_count = models.PositiveSmallIntegerField("Число уроков", default=0)
    is_published = models.BooleanField("Опубликован", default=True)
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлён", auto_now=True)

    class Meta:
        verbose_name = "Модуль"
        verbose_name_plural = "Модули"
        db_table = "academy_module"
        ordering = ["sort_order"]
        constraints = [
            models.UniqueConstraint(
                fields=["program", "sort_order"],
                name="academy_module_program_sort_unique",
            ),
        ]

    def __str__(self):
        return f"{self.program.slug} · {self.title}"


class Lesson(models.Model):
    module = models.ForeignKey(
        Module,
        on_delete=models.CASCADE,
        related_name="lessons",
        verbose_name="Модуль",
    )
    sort_order = models.SmallIntegerField(
        "Порядок",
        help_text="Порядок урока в модуле: 1, 2, 3…",
    )
    title = models.CharField("Название урока", max_length=255)
    description = models.TextField(
        "Описание",
        blank=True,
        null=True,
        help_text="О чём урок (можно коротко).",
    )
    result_description = models.TextField(
        "Результат урока",
        blank=True,
        null=True,
        help_text="Что ученик получит после прохождения — показывается в карточке урока.",
    )
    lesson_type = models.CharField(
        "Тип урока",
        max_length=20,
        choices=LESSON_TYPE_CHOICES,
        default=LESSON_TYPE_VIDEO,
    )
    duration_minutes = models.PositiveSmallIntegerField(
        "Длительность (мин)",
        null=True,
        blank=True,
        help_text="Примерная длина в минутах, например 12.",
    )
    video_url = models.TextField(
        "Ссылка на видео",
        blank=True,
        null=True,
        help_text="Внешняя ссылка (CDN/YouTube-direct mp4) или путь /media/lessons/…. Если загружен файл ниже — файл имеет приоритет.",
    )
    video_file = models.FileField(
        "Файл видео",
        upload_to="lessons/",
        blank=True,
        null=True,
        help_text="Загрузите mp4/webm — файл попадёт в /media/lessons/ и подставится в ссылку. Имя лучше латиницей без пробелов.",
    )
    video_quality = models.CharField(
        "Качество видео",
        max_length=10,
        blank=True,
        null=True,
        help_text="Подпись качества, например HD. Можно оставить пустым.",
    )
    ibox_scenario_id = models.BigIntegerField(
        "Сценарий AI Hub",
        null=True,
        blank=True,
        help_text="ID сценария AI Hub, если урок связан с чатом. Обычно пусто.",
    )
    is_published = models.BooleanField("Опубликован", default=True)
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлён", auto_now=True)

    class Meta:
        verbose_name = "Урок"
        verbose_name_plural = "Уроки"
        db_table = "academy_lesson"
        ordering = ["sort_order"]
        constraints = [
            models.UniqueConstraint(
                fields=["module", "sort_order"],
                name="academy_lesson_module_sort_unique",
            ),
        ]

    def __str__(self):
        return self.title

    @property
    def program(self):
        return self.module.program

    @property
    def resolved_video_url(self) -> str | None:
        """Публичный URL для плеера. Файл имеет приоритет; битые /media/ пути не отдаём."""
        if self.video_file:
            try:
                if self.video_file.name and self.video_file.storage.exists(self.video_file.name):
                    url = self.video_file.url or ""
                    if url.startswith(("http://", "https://")):
                        return url
                    if url:
                        return url if url.startswith("/") else f"/{url}"
            except Exception:
                pass

        url = (self.video_url or "").strip()
        if not url:
            return None
        if url.startswith(("http://", "https://")):
            return url

        # Локальный путь вида /media/lessons/….mp4 — только если файл реально есть.
        media_prefix = "/media/"
        if url.startswith(media_prefix):
            from pathlib import Path

            from django.conf import settings

            relative = url[len(media_prefix) :].lstrip("/")
            full = Path(settings.MEDIA_ROOT) / relative
            if full.is_file():
                return url if url.startswith("/") else f"/{url}"
            return None

        return url

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # После загрузки файла подставляем публичный путь в video_url —
        # так в админке видно ту же ссылку, что открывает плеер.
        if self.video_file:
            public = self.resolved_video_url
            if public and self.video_url != public:
                Lesson.objects.filter(pk=self.pk).update(video_url=public)
                self.video_url = public


class LessonResource(models.Model):
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name="resources",
        verbose_name="Урок",
    )
    resource_type = models.CharField("Тип материала", max_length=30, choices=RESOURCE_TYPE_CHOICES)
    title = models.CharField("Название", max_length=255)
    file_url = models.TextField(
        "Ссылка на файл",
        blank=True,
        null=True,
        help_text="URL файла или путь /media/…",
    )
    content = models.TextField(
        "Текст",
        blank=True,
        null=True,
        help_text="Текст задания или конспекта, если нет файла.",
    )
    sort_order = models.SmallIntegerField("Порядок", default=0)
    created_at = models.DateTimeField("Создан", auto_now_add=True)

    class Meta:
        verbose_name = "Материал урока"
        verbose_name_plural = "Материалы уроков"
        db_table = "academy_lesson_resource"
        ordering = ["sort_order", "id"]
        indexes = [
            models.Index(fields=["lesson", "resource_type"]),
        ]

    def __str__(self):
        return f"{self.lesson_id} · {self.title}"


class UserProgress(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="academy_program_progress",
        verbose_name="Пользователь",
    )
    program = models.ForeignKey(
        Program,
        on_delete=models.CASCADE,
        related_name="user_progress",
        verbose_name="Программа",
    )
    completed_lessons = models.PositiveSmallIntegerField("Пройдено уроков", default=0)
    completed_modules = models.PositiveSmallIntegerField("Пройдено модулей", default=0)
    progress_percent = models.PositiveSmallIntegerField("Прогресс %", default=0)
    status = models.CharField(
        "Статус",
        max_length=20,
        choices=PROGRESS_STATUS_CHOICES,
        default=STATUS_NOT_STARTED,
    )
    last_lesson = models.ForeignKey(
        Lesson,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="Последний урок",
    )
    started_at = models.DateTimeField("Начато", null=True, blank=True)
    completed_at = models.DateTimeField("Завершено", null=True, blank=True)
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    class Meta:
        verbose_name = "Прогресс по программе"
        verbose_name_plural = "Прогресс по программам"
        db_table = "academy_user_progress"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "program"],
                name="academy_user_progress_unique",
            ),
        ]
        indexes = [
            models.Index(fields=["user", "status"]),
        ]

    def __str__(self):
        return f"UserProgress {self.user_id} · {self.program.slug}"


class ModuleProgress(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="academy_module_progress",
        verbose_name="Пользователь",
    )
    module = models.ForeignKey(
        Module,
        on_delete=models.CASCADE,
        related_name="user_progress",
        verbose_name="Модуль",
    )
    completed_lessons = models.PositiveSmallIntegerField("Пройдено уроков", default=0)
    status = models.CharField(
        "Статус",
        max_length=20,
        choices=PROGRESS_STATUS_CHOICES,
        default=STATUS_NOT_STARTED,
    )
    completed_at = models.DateTimeField("Завершено", null=True, blank=True)
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    class Meta:
        verbose_name = "Прогресс по модулю"
        verbose_name_plural = "Прогресс по модулям"
        db_table = "academy_module_progress"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "module"],
                name="academy_module_progress_unique",
            ),
        ]

    def __str__(self):
        return f"ModuleProgress {self.user_id} · {self.module_id}"


class LessonProgress(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="academy_lesson_progress",
        verbose_name="Пользователь",
    )
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name="user_progress",
        verbose_name="Урок",
    )
    status = models.CharField(
        "Статус",
        max_length=20,
        choices=PROGRESS_STATUS_CHOICES,
        default=STATUS_NOT_STARTED,
    )
    video_position_sec = models.PositiveIntegerField("Позиция в видео (сек)", default=0)
    started_at = models.DateTimeField("Начато", null=True, blank=True)
    completed_at = models.DateTimeField("Завершено", null=True, blank=True)
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    class Meta:
        verbose_name = "Прогресс по уроку"
        verbose_name_plural = "Прогресс по урокам"
        db_table = "academy_lesson_progress"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "lesson"],
                name="academy_lesson_progress_unique",
            ),
        ]

    def __str__(self):
        return f"LessonProgress {self.user_id} · {self.lesson_id}"
