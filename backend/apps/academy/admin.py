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


class NestedLessonInline(TabularInline):
    """Уроки внутри модуля на странице программы (один уровень вложенности Unfold)."""

    model = Lesson
    extra = 1
    fields = (
        "sort_order",
        "title",
        "duration_minutes",
        "video_url",
        "is_published",
    )
    show_change_link = True
    # video_file только на странице урока: вложенные inline часто не сохраняют FileField.


class ModuleInline(StackedInline):
    model = Module
    extra = 1
    fields = ("sort_order", "title", "description", "is_intro", "is_published")
    show_change_link = True
    inlines = [NestedLessonInline]


@admin.register(Program)
class ProgramAdmin(ModelAdmin):
    section_description = (
        "Создание на одной странице: название → модули → в каждом модуле уроки (название + ссылка на видео) → "
        "включите «Опубликована». В демо все опубликованные программы открыты в кабинете без тарифа."
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
        for module in form.instance.modules.all():
            ProgramCatalogService.refresh_module_lesson_count(module)
        ProgramCatalogService.refresh_counts(form.instance)


class LessonInline(TabularInline):
    model = Lesson
    extra = 1
    fields = (
        "sort_order",
        "title",
        "lesson_type",
        "duration_minutes",
        "video_url",
        "video_quality",
        "is_published",
    )
    show_change_link = True
    # Загрузка файла — только на странице «Уроки» (show_change_link).


@admin.register(Module)
class ModuleAdmin(ModelAdmin):
    section_description = (
        "Модуль можно править и отдельно. Уроки — ниже на этой странице. "
        "Удобнее создавать программу целиком на странице «Программы»."
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


class LessonResourceInline(TabularInline):
    model = LessonResource
    extra = 0
    fields = ("sort_order", "resource_type", "title", "file_url", "content")


@admin.register(Lesson)
class LessonAdmin(ModelAdmin):
    section_description = (
        "Чтобы видео появилось в кабинете: откройте урок → «Файл видео» → загрузите mp4 → Сохранить. "
        "Не вставляйте путь /media/... вручную, если файла ещё нет на сервере."
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
        (None, {"fields": ("module", "sort_order", "title", "description", "result_description", "lesson_type", "duration_minutes", "is_published")}),
        (
            "Видео",
            {
                "fields": ("video_file", "video_url", "video_quality"),
                "description": (
                    "1) Загрузите mp4/webm в «Файл видео» и нажмите Сохранить. "
                    "Ссылка /media/lessons/… подставится сама. "
                    "2) Либо вставьте прямую https-ссылку на mp4. "
                    "Имя файла — латиницей без пробелов. "
                    "Тест: https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4"
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
        if obj.resolved_video_url:
            self.message_user(request, f"Видео доступно: {obj.resolved_video_url}")
        elif obj.video_file or obj.video_url:
            self.message_user(
                request,
                "Файл/ссылка указаны, но видео недоступно (файл не найден на диске или ссылка битая).",
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
