from django.core.management.base import BaseCommand

from apps.academy.constants import (
    LESSON_TYPE_VIDEO,
    RESOURCE_PRACTICE,
    RESOURCE_SUMMARY,
    RESOURCE_TEMPLATE,
)
from apps.academy.models import Lesson, LessonResource, Module, Program
from apps.academy.services import ProgramCatalogService

GPT_NEW_MODULES = [
    {
        "sort_order": 0,
        "title": "Введение в ChatGPT",
        "description": "Как устроена программа, что понадобится и с чего начать",
        "is_intro": True,
        "lessons": [
            {
                "sort_order": 1,
                "title": "Введение в ChatGPT",
                "description": "Обзор программы и первые шаги",
                "result_description": (
                    "Вы разберёте ключевые принципы и увидите рабочий пример "
                    "по структуре RE:RISE."
                ),
                "duration_minutes": 9,
                # Публичный тестовый mp4 — чтобы админка/портал сразу воспроизводили ролик без локальных файлов.
                "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
            },
        ],
    },
    {
        "sort_order": 1,
        "title": "Знакомство с ChatGPT",
        "description": "Первые шаги и базовые принципы работы",
        "lessons": [
            {"sort_order": 1, "title": "Что такое ChatGPT и как он работает", "duration_minutes": 15},
            {"sort_order": 2, "title": "Первый диалог с ChatGPT", "duration_minutes": 12},
            {"sort_order": 3, "title": "Промпты: структура и лучшие практики", "duration_minutes": 18},
            {"sort_order": 4, "title": "Типичные ошибки новичков", "duration_minutes": 14},
        ],
    },
    {
        "sort_order": 2,
        "title": "ChatGPT для контента",
        "description": "Тексты, посты и сценарии",
        "lessons": [
            {"sort_order": 1, "title": "Генерация постов для соцсетей", "duration_minutes": 20},
            {"sort_order": 2, "title": "Сценарии для видео и сторис", "duration_minutes": 16},
            {"sort_order": 3, "title": "Редактирование и улучшение текстов", "duration_minutes": 17},
            {"sort_order": 4, "title": "Контент-план на неделю", "duration_minutes": 22},
        ],
    },
    {
        "sort_order": 3,
        "title": "ChatGPT для бизнеса",
        "description": "Продажи, офферы и коммуникация",
        "lessons": [
            {"sort_order": 1, "title": "Офферы и коммерческие предложения", "duration_minutes": 19},
            {"sort_order": 2, "title": "Ответы клиентам и возражения", "duration_minutes": 21},
            {"sort_order": 3, "title": "Автоматизация рутинных задач", "duration_minutes": 18},
            {"sort_order": 4, "title": "Шаблоны для партнёрской работы", "duration_minutes": 16},
        ],
    },
    {
        "sort_order": 4,
        "title": "Продвинутые техники",
        "description": "Цепочки промптов и кастомные роли",
        "lessons": [
            {"sort_order": 1, "title": "Системные промпты и роли", "duration_minutes": 24},
            {"sort_order": 2, "title": "Многошаговые сценарии", "duration_minutes": 20},
            {"sort_order": 3, "title": "Работа с документами и данными", "duration_minutes": 23},
            {"sort_order": 4, "title": "Интеграция в рабочий процесс", "duration_minutes": 19},
        ],
    },
    {
        "sort_order": 5,
        "title": "Модуль 6",
        "description": "Финальные техники и коммерческое применение",
        "lessons": [
            {"sort_order": 1, "title": "Коммерческие кейсы RE:RISE", "duration_minutes": 28},
            {"sort_order": 2, "title": "Масштабирование результатов", "duration_minutes": 25},
            {
                "sort_order": 3,
                "title": "Как быстро и стабильно выполнять заказы",
                "duration_minutes": 36,
            },
            {"sort_order": 4, "title": "Итоги программы и следующие шаги", "duration_minutes": 15},
        ],
    },
]

PROGRAMS = [
    {
        "slug": "gpt-new",
        "title": "GPT - NEW",
        "description": "ChatGPT с нуля до коммерческого применения",
        "icon": "chat",
        "tags": ["HIT"],
        "required_tariff": "rise",
        "sort_order": 0,
        "modules": GPT_NEW_MODULES,
    },
    {
        "slug": "ai-design",
        "title": "AI Design",
        "description": "Дизайн с помощью нейросетей",
        "icon": "design",
        "tags": [],
        "required_tariff": "rise-pro",
        "sort_order": 1,
        "modules": [
            {
                "sort_order": 0,
                "title": "Введение в AI Design",
                "is_intro": True,
                "lessons": [
                    {"sort_order": 1, "title": "Инструменты и возможности", "duration_minutes": 10},
                ],
            },
            {
                "sort_order": 1,
                "title": "Генерация изображений",
                "lessons": [
                    {"sort_order": 1, "title": "Промпты для Midjourney", "duration_minutes": 15},
                    {"sort_order": 2, "title": "Стили и референсы", "duration_minutes": 12},
                ],
            },
        ],
    },
    {
        "slug": "ai-video",
        "title": "AI Video",
        "description": "Видео-контент с нейросетями",
        "icon": "video",
        "tags": [],
        "required_tariff": "rise-pro-max",
        "sort_order": 2,
        "modules": [
            {
                "sort_order": 0,
                "title": "Введение",
                "is_intro": True,
                "lessons": [
                    {"sort_order": 1, "title": "Обзор AI Video", "duration_minutes": 8},
                ],
            },
        ],
    },
]


class Command(BaseCommand):
    help = "Seed academy programs (GPT-NOW mock + 2 доп. программы)"

    def handle(self, *args, **options):
        for item in PROGRAMS:
            program_data = dict(item)
            modules_data = program_data.pop("modules")
            program, created = Program.objects.update_or_create(
                slug=program_data["slug"],
                defaults={
                    **program_data,
                    "is_published": True,
                },
            )
            action = "Created" if created else "Updated"
            self.stdout.write(f"{action} program: {program.slug}")

            for module_item in modules_data:
                module_data = dict(module_item)
                lessons_data = module_data.pop("lessons")
                module, _ = Module.objects.update_or_create(
                    program=program,
                    sort_order=module_data["sort_order"],
                    defaults={
                        **module_data,
                        "is_published": True,
                    },
                )

                for lesson_data in lessons_data:
                    defaults = {
                        "title": lesson_data["title"],
                        "description": lesson_data.get("description", ""),
                        "result_description": lesson_data.get("result_description", ""),
                        "duration_minutes": lesson_data.get("duration_minutes"),
                        "video_quality": "HD",
                        "lesson_type": LESSON_TYPE_VIDEO,
                        "is_published": True,
                    }
                    # video_url только при создании или если в сиде явно задан рабочий URL.
                    # Иначе не затираем загруженный через админку файл / ссылку.
                    explicit_video = lesson_data.get("video_url")
                    if explicit_video:
                        defaults["video_url"] = explicit_video

                    lesson, lesson_created = Lesson.objects.update_or_create(
                        module=module,
                        sort_order=lesson_data["sort_order"],
                        defaults=defaults,
                    )
                    if lesson_created and not explicit_video:
                        # Раньше сюда писали фейковый /media/… — больше не пишем.
                        Lesson.objects.filter(pk=lesson.pk).update(video_url="")
                        lesson.video_url = ""
                    elif (
                        not lesson_created
                        and not lesson.video_file
                        and (lesson.video_url or "").startswith("/media/")
                    ):
                        from pathlib import Path

                        from django.conf import settings

                        relative = lesson.video_url[len("/media/") :].lstrip("/")
                        if not (Path(settings.MEDIA_ROOT) / relative).is_file():
                            Lesson.objects.filter(pk=lesson.pk).update(video_url="")
                            lesson.video_url = ""

                    if lesson_created and module.sort_order == 0 and lesson.sort_order == 1:
                        LessonResource.objects.get_or_create(
                            lesson=lesson,
                            resource_type=RESOURCE_SUMMARY,
                            defaults={
                                "title": "Краткий конспект",
                                "file_url": f"/media/lessons/{program.slug}-summary.pdf",
                                "sort_order": 0,
                            },
                        )
                        LessonResource.objects.get_or_create(
                            lesson=lesson,
                            resource_type=RESOURCE_TEMPLATE,
                            defaults={
                                "title": "Рабочий шаблон",
                                "file_url": f"/media/lessons/{program.slug}-template.docx",
                                "sort_order": 1,
                            },
                        )
                        LessonResource.objects.get_or_create(
                            lesson=lesson,
                            resource_type=RESOURCE_PRACTICE,
                            defaults={
                                "title": "Практическое задание",
                                "file_url": None,
                                "sort_order": 2,
                            },
                        )

                ProgramCatalogService.refresh_module_lesson_count(module)

            ProgramCatalogService.refresh_counts(program)
            self.stdout.write(
                self.style.SUCCESS(
                    f"  {program.module_count} modules, {program.lesson_count} lessons"
                )
            )

        self.stdout.write(self.style.SUCCESS("Academy seed complete."))
