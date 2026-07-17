from django.core.management.base import BaseCommand

from apps.academy.constants import LESSON_TYPE_VIDEO, RESOURCE_SUMMARY
from apps.academy.models import Lesson, LessonResource, Module, Program
from apps.academy.services import ProgramCatalogService

# Публичные короткие sample mp4 (Google sample bucket) — только для демо-просмотра.
SAMPLE = "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample"


class Command(BaseCommand):
    help = "Создаёт демо-курс «Первые шаги» с 2 модулями и 5 уроками"

    def handle(self, *args, **options):
        program, created = Program.objects.update_or_create(
            slug="first-steps",
            defaults={
                "title": "Первые шаги в RE:RISE",
                "description": (
                    "Короткий демо-курс: как устроен кабинет, с чего начать обучение "
                    "и как пройти первый урок с видео."
                ),
                "icon": "rocket",
                "tags": ["DEMO", "Старт"],
                "required_tariff": "rise",
                "is_published": True,
                "sort_order": -1,
            },
        )
        action = "Created" if created else "Updated"
        self.stdout.write(f"{action} program: {program.slug}")

        modules_spec = [
            {
                "sort_order": 0,
                "title": "Знакомство с кабинетом",
                "description": "Ориентация: что где лежит и как пользоваться обучением",
                "is_intro": True,
                "lessons": [
                    {
                        "sort_order": 1,
                        "title": "Добро пожаловать в RE:RISE",
                        "description": "Короткий обзор: зачем этот курс и что будет дальше.",
                        "result_description": "Понимаете структуру курса и куда нажимать в кабинете.",
                        "duration_minutes": 4,
                        "video_url": f"{SAMPLE}/ForBiggerBlazes.mp4",
                    },
                    {
                        "sort_order": 2,
                        "title": "Академия: программы и прогресс",
                        "description": "Как открыть программу, увидеть модули и отметить урок пройденным.",
                        "result_description": "Умеете открыть урок и зафиксировать прогресс.",
                        "duration_minutes": 6,
                        "video_url": f"{SAMPLE}/ForBiggerEscapes.mp4",
                    },
                ],
            },
            {
                "sort_order": 1,
                "title": "Первая практика",
                "description": "Несколько коротких уроков с видео — как будет выглядеть боевой курс",
                "is_intro": False,
                "lessons": [
                    {
                        "sort_order": 1,
                        "title": "Как устроен видеоурок",
                        "description": "Плеер, материалы к уроку, кнопка «пройден».",
                        "result_description": "Знаете, из каких частей состоит урок.",
                        "duration_minutes": 5,
                        "video_url": f"{SAMPLE}/ForBiggerFun.mp4",
                    },
                    {
                        "sort_order": 2,
                        "title": "Свои ролики вместо демо",
                        "description": "Куда класть файлы: админка → «Файл видео» или папка media/lessons/.",
                        "result_description": "Можете заменить демо-ролик на свой mp4.",
                        "duration_minutes": 5,
                        "video_url": f"{SAMPLE}/ForBiggerJoyrides.mp4",
                    },
                    {
                        "sort_order": 3,
                        "title": "Что дальше",
                        "description": "Краткий итог демо-курса и следующие шаги в продукте.",
                        "result_description": "Готовы собирать полноценные программы в админке.",
                        "duration_minutes": 3,
                        "video_url": f"{SAMPLE}/ForBiggerMeltdowns.mp4",
                    },
                ],
            },
        ]

        for module_item in modules_spec:
            lessons_data = module_item.pop("lessons")
            module, _ = Module.objects.update_or_create(
                program=program,
                sort_order=module_item["sort_order"],
                defaults={
                    **module_item,
                    "is_published": True,
                },
            )
            for lesson_data in lessons_data:
                lesson, lesson_created = Lesson.objects.update_or_create(
                    module=module,
                    sort_order=lesson_data["sort_order"],
                    defaults={
                        "title": lesson_data["title"],
                        "description": lesson_data.get("description", ""),
                        "result_description": lesson_data.get("result_description", ""),
                        "duration_minutes": lesson_data.get("duration_minutes"),
                        "video_url": lesson_data["video_url"],
                        "video_quality": "HD",
                        "lesson_type": LESSON_TYPE_VIDEO,
                        "is_published": True,
                    },
                )
                if lesson_created and module.sort_order == 0 and lesson.sort_order == 1:
                    LessonResource.objects.get_or_create(
                        lesson=lesson,
                        resource_type=RESOURCE_SUMMARY,
                        defaults={
                            "title": "Краткий конспект старта",
                            "content": "1) Откройте программу\n2) Смотрите урок\n3) Отметьте пройденным",
                            "sort_order": 0,
                        },
                    )
            ProgramCatalogService.refresh_module_lesson_count(module)

        ProgramCatalogService.refresh_counts(program)
        self.stdout.write(
            self.style.SUCCESS(
                f"Готово: {program.title} — {program.module_count} модулей, {program.lesson_count} уроков. "
                f"Откройте в кабинете /courses/first-steps"
            )
        )
