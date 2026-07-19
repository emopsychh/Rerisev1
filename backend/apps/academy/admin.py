from django.contrib import admin, messages

from core.admin import ModelAdmin, StackedInline, TabularInline
from apps.academy.models import (
    Lesson,
    LessonProgress,
    LessonResource,
    Module,
    ModuleProgress,
    Program,
    UserProgress,
)
from apps.academy.services import ProgramCatalogService


def _sync_lesson_video_url(lesson: Lesson) -> str | None:
    """После загрузки файла подставляет публичный /media/… в video_url."""
    if not lesson.video_file:
        return lesson.resolved_video_url
    public = lesson.resolved_video_url
    if public and lesson.video_url != public:
        Lesson.objects.filter(pk=lesson.pk).update(video_url=public)
        lesson.video_url = public
    return public


class NestedLessonInline(TabularInline):
    """Уроки внутри модуля на странице программы."""

    model = Lesson
    extra = 1
    fields = (
        "sort_order",
        "title",
        "duration_minutes",
        "video_file",
        "video_url",
        "is_published",
    )
    show_change_link = True


class ModuleInline(StackedInline):
    model = Module
    extra = 1
    fields = ("sort_order", "title", "description", "is_intro", "is_published")
    show_change_link = True
    inlines = [NestedLessonInline]


@admin.register(Program)
class ProgramAdmin(ModelAdmin):
    section_description = (
        "Программа → модули → уроки. Видео можно загрузить кнопкой «Файл видео» прямо в списке уроков "
        "или открыть урок отдельно. После выбора файла нажмите «Сохранить»."
    )
    list_display = (
        "slug",
        "title",
        "module_count",
        "lesson_count",
        "required_tariff",
        "is_published",
        "sort_order",
    )
    list_filter = ("is_published", "required_tariff")
    search_fields = ("slug", "title")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("module_count", "lesson_count")
    inlines = [ModuleInline]
    fieldsets = (
        (
            "Основное",
            {
                "description": "Название видно ученикам. Slug заполнится сам. Описание — текст на карточке.",
                "fields": ("title", "slug", "description", "sort_order", "is_published"),
            },
        ),
        (
            "Оформление",
            {
                "description": 'Теги — JSON, например ["HIT"]. Иконку можно не заполнять.',
                "fields": ("tags", "icon"),
                "classes": ("collapse",),
            },
        ),
        (
            "Доступ (в демо можно не трогать)",
            {
                "description": "В демо-режиме тариф не блокирует просмотр. Позже: rise / rise-pro / rise-pro-max.",
                "fields": ("required_tariff", "required_product"),
                "classes": ("collapse",),
            },
        ),
        (
            "Счётчики (считаются сами)",
            {
                "fields": ("module_count", "lesson_count"),
                "classes": ("collapse",),
            },
        ),
    )

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        synced = 0
        for module in form.instance.modules.all():
            ProgramCatalogService.refresh_module_lesson_count(module)
            for lesson in module.lessons.all():
                if lesson.video_file and _sync_lesson_video_url(lesson):
                    synced += 1
        ProgramCatalogService.refresh_counts(form.instance)
        if synced:
            self.message_user(request, f"Видео синхронизировано у уроков: {synced}")


class LessonInline(TabularInline):
    model = Lesson
    extra = 1
    fields = (
        "sort_order",
        "title",
        "lesson_type",
        "duration_minutes",
        "video_file",
        "video_url",
        "video_quality",
        "is_published",
    )
    show_change_link = True


@admin.register(Module)
class ModuleAdmin(ModelAdmin):
    section_description = (
        "Уроки модуля ниже. Загрузите mp4 кнопкой «Файл видео» и нажмите «Сохранить» внизу страницы."
    )
    list_display = ("program", "sort_order", "title", "lesson_count", "is_intro", "is_published")
    list_filter = ("is_intro", "is_published", "program")
    search_fields = ("title", "program__slug")
    readonly_fields = ("lesson_count",)
    inlines = [LessonInline]

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        ProgramCatalogService.refresh_module_lesson_count(form.instance)
        ProgramCatalogService.refresh_counts(form.instance.program)
        synced = 0
        for lesson in form.instance.lessons.all():
            if lesson.video_file and _sync_lesson_video_url(lesson):
                synced += 1
        if synced:
            self.message_user(request, f"Видео синхронизировано у уроков: {synced}")


class LessonResourceInline(TabularInline):
    model = LessonResource
    extra = 0
    fields = ("sort_order", "resource_type", "title", "file_url", "content")


@admin.register(Lesson)
class LessonAdmin(ModelAdmin):
    section_description = (
        "Загрузка видео: выберите файл в «Файл видео» → Сохранить. "
        "Либо вставьте прямую https-ссылку на mp4. Через SSH загружать не нужно."
    )
    list_display = (
        "title",
        "module",
        "sort_order",
        "lesson_type",
        "duration_minutes",
        "has_video",
        "is_published",
    )
    list_filter = ("lesson_type", "is_published", "module__program")
    search_fields = ("title", "module__title", "module__program__slug")
    inlines = [LessonResourceInline]
    fieldsets = (
        (
            "Видео",
            {
                "fields": ("video_file", "video_url", "video_quality"),
                "description": (
                    "Нажмите «Выберите файл» / Choose file у поля «Файл видео», выберите mp4 или webm, "
                    "затем «Сохранить» внизу. Ссылка /media/lessons/… появится сама. "
                    "Имя файла лучше латиницей без пробелов. "
                    "Альтернатива: прямая https-ссылка на mp4."
                ),
            },
        ),
        (
            None,
            {
                "fields": (
                    "module",
                    "sort_order",
                    "title",
                    "description",
                    "result_description",
                    "lesson_type",
                    "duration_minutes",
                    "is_published",
                ),
            },
        ),
        ("AI Hub", {"fields": ("ibox_scenario_id",)}),
    )

    @admin.display(boolean=True, description="Видео")
    def has_video(self, obj: Lesson) -> bool:
        return bool(obj.resolved_video_url)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        ProgramCatalogService.refresh_module_lesson_count(obj.module)
        ProgramCatalogService.refresh_counts(obj.module.program)
        public = _sync_lesson_video_url(obj)
        file_changed = "video_file" in getattr(form, "changed_data", [])
        if file_changed:
            if public:
                self.message_user(
                    request,
                    f"Видео загружено и доступно: {public}",
                    level=messages.SUCCESS,
                )
            else:
                self.message_user(
                    request,
                    "Файл принят формой, но не найден в media. Проверьте том media_data и права записи.",
                    level=messages.ERROR,
                )
        elif public:
            self.message_user(request, f"Видео доступно: {public}")
        elif obj.video_url:
            self.message_user(
                request,
                "Указана ссылка, но файл по /media/ не найден. Загрузите файл кнопкой «Файл видео» "
                "или укажите рабочую https-ссылку.",
                level=messages.WARNING,
            )


@admin.register(UserProgress)
class UserProgressAdmin(ModelAdmin):
    section_description = "Сколько человек прошёл по всей программе: процент, статус, сколько уроков закрыто."
    list_display = ("user", "program", "progress_percent", "status", "completed_lessons")
    list_filter = ("status",)
    search_fields = ("user__email", "program__slug")


@admin.register(ModuleProgress)
class ModuleProgressAdmin(ModelAdmin):
    section_description = "Прогресс внутри одного модуля — удобно, если нужно понять, где человек «застрял»."
    list_display = ("user", "module", "completed_lessons", "status")
    list_filter = ("status",)


@admin.register(LessonProgress)
class LessonProgressAdmin(ModelAdmin):
    section_description = "Статус конкретного урока у пользователя и позиция в видео (если сохраняли)."
    list_display = ("user", "lesson", "status", "video_position_sec")
    list_filter = ("status",)
