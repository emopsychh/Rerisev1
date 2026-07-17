from django.db import transaction
from django.utils import timezone

from apps.academy.access import user_has_program_access
from apps.academy.constants import STATUS_COMPLETED, STATUS_IN_PROGRESS, STATUS_NOT_STARTED
from apps.academy.models import Lesson, LessonProgress, Module, ModuleProgress, Program, UserProgress
from apps.academy.selectors import find_next_lesson
from apps.users.models import User


class AcademyAccessError(PermissionError):
    pass


class ProgressService:
    @staticmethod
    @transaction.atomic
    def start_lesson(user: User, lesson: Lesson) -> LessonProgress:
        ProgressService._ensure_access(user, lesson)

        now = timezone.now()
        lesson_progress, created = LessonProgress.objects.get_or_create(
            user=user,
            lesson=lesson,
            defaults={
                "status": STATUS_IN_PROGRESS,
                "started_at": now,
            },
        )
        if not created and lesson_progress.status == STATUS_NOT_STARTED:
            lesson_progress.status = STATUS_IN_PROGRESS
            lesson_progress.started_at = lesson_progress.started_at or now
            lesson_progress.save(update_fields=["status", "started_at", "updated_at"])

        program = lesson.module.program
        user_progress, up_created = UserProgress.objects.get_or_create(
            user=user,
            program=program,
            defaults={
                "status": STATUS_IN_PROGRESS,
                "started_at": now,
                "last_lesson": lesson,
            },
        )
        if not up_created:
            updates = {"last_lesson": lesson, "updated_at": now}
            if user_progress.status == STATUS_NOT_STARTED:
                user_progress.status = STATUS_IN_PROGRESS
                user_progress.started_at = user_progress.started_at or now
                updates["status"] = STATUS_IN_PROGRESS
                updates["started_at"] = user_progress.started_at
            user_progress.last_lesson = lesson
            user_progress.save(update_fields=list(updates.keys()))

        module_progress, mp_created = ModuleProgress.objects.get_or_create(
            user=user,
            module=lesson.module,
            defaults={"status": STATUS_IN_PROGRESS},
        )
        if not mp_created and module_progress.status == STATUS_NOT_STARTED:
            module_progress.status = STATUS_IN_PROGRESS
            module_progress.save(update_fields=["status", "updated_at"])

        return lesson_progress

    @staticmethod
    @transaction.atomic
    def update_video_position(user: User, lesson: Lesson, position_sec: int) -> LessonProgress:
        ProgressService._ensure_access(user, lesson)

        lesson_progress, _ = LessonProgress.objects.get_or_create(
            user=user,
            lesson=lesson,
            defaults={"status": STATUS_IN_PROGRESS, "started_at": timezone.now()},
        )
        lesson_progress.video_position_sec = max(position_sec, 0)
        if lesson_progress.status == STATUS_NOT_STARTED:
            lesson_progress.status = STATUS_IN_PROGRESS
            lesson_progress.started_at = timezone.now()
        lesson_progress.save(
            update_fields=["video_position_sec", "status", "started_at", "updated_at"]
        )
        return lesson_progress

    @staticmethod
    @transaction.atomic
    def complete_lesson(user: User, lesson: Lesson) -> dict:
        ProgressService._ensure_access(user, lesson)

        now = timezone.now()
        lesson_progress, _ = LessonProgress.objects.get_or_create(
            user=user,
            lesson=lesson,
        )
        was_completed = lesson_progress.status == STATUS_COMPLETED
        if not was_completed:
            lesson_progress.status = STATUS_COMPLETED
            lesson_progress.completed_at = now
            lesson_progress.started_at = lesson_progress.started_at or now
            lesson_progress.save(
                update_fields=["status", "completed_at", "started_at", "updated_at"]
            )

        module_progress = ProgressService._recalculate_module(user, lesson.module)
        program_progress = ProgressService._recalculate_program(user, lesson.module.program)

        next_lesson = find_next_lesson(lesson)
        user_progress = UserProgress.objects.get(user=user, program=lesson.module.program)
        user_progress.last_lesson = next_lesson or lesson
        user_progress.save(update_fields=["last_lesson", "updated_at"])

        next_payload = None
        if next_lesson:
            next_payload = {
                "id": next_lesson.id,
                "title": next_lesson.title,
                "module_title": next_lesson.module.title,
            }

        return {
            "lesson_id": lesson.id,
            "status": STATUS_COMPLETED,
            "completed_at": lesson_progress.completed_at.isoformat().replace("+00:00", "Z"),
            "program_progress": {
                "completed_lessons": program_progress.completed_lessons,
                "completed_modules": program_progress.completed_modules,
                "percent": program_progress.progress_percent,
                "status": program_progress.status,
            },
            "module_progress": {
                "completed_lessons": module_progress.completed_lessons,
                "status": module_progress.status,
            },
            "next_lesson": next_payload,
        }

    @staticmethod
    def _ensure_access(user: User, lesson: Lesson) -> None:
        program = lesson.module.program
        if not user_has_program_access(user, program):
            raise AcademyAccessError("Нет доступа к этой программе")

    @staticmethod
    def _recalculate_module(user: User, module: Module) -> ModuleProgress:
        completed_count = LessonProgress.objects.filter(
            user=user,
            lesson__module=module,
            status=STATUS_COMPLETED,
        ).count()

        module_progress, _ = ModuleProgress.objects.get_or_create(
            user=user,
            module=module,
        )
        module_progress.completed_lessons = completed_count
        if completed_count >= module.lesson_count and module.lesson_count > 0:
            module_progress.status = STATUS_COMPLETED
            module_progress.completed_at = module_progress.completed_at or timezone.now()
        elif completed_count > 0:
            module_progress.status = STATUS_IN_PROGRESS
        else:
            module_progress.status = STATUS_NOT_STARTED
            module_progress.completed_at = None

        module_progress.save(
            update_fields=["completed_lessons", "status", "completed_at", "updated_at"]
        )
        return module_progress

    @staticmethod
    def _recalculate_program(user: User, program: Program) -> UserProgress:
        completed_lessons = LessonProgress.objects.filter(
            user=user,
            lesson__module__program=program,
            status=STATUS_COMPLETED,
        ).count()

        completed_modules = (
            ModuleProgress.objects.filter(
                user=user,
                module__program=program,
                status=STATUS_COMPLETED,
            ).count()
        )

        total_lessons = program.lesson_count
        if total_lessons > 0:
            percent = min(100, int(completed_lessons * 100 / total_lessons))
        else:
            percent = 0

        user_progress, _ = UserProgress.objects.get_or_create(
            user=user,
            program=program,
        )
        user_progress.completed_lessons = completed_lessons
        user_progress.completed_modules = completed_modules
        user_progress.progress_percent = percent

        if completed_lessons >= program.lesson_count and program.lesson_count > 0:
            user_progress.status = STATUS_COMPLETED
            user_progress.completed_at = user_progress.completed_at or timezone.now()
        elif completed_lessons > 0:
            user_progress.status = STATUS_IN_PROGRESS
            user_progress.started_at = user_progress.started_at or timezone.now()
        else:
            user_progress.status = STATUS_NOT_STARTED

        user_progress.save(
            update_fields=[
                "completed_lessons",
                "completed_modules",
                "progress_percent",
                "status",
                "started_at",
                "completed_at",
                "updated_at",
            ]
        )
        return user_progress


class ProgramCatalogService:
    @staticmethod
    def refresh_counts(program: Program) -> Program:
        modules = Module.objects.filter(program=program, is_published=True)
        lesson_count = Lesson.objects.filter(
            module__program=program,
            is_published=True,
            module__is_published=True,
        ).count()
        program.module_count = modules.count()
        program.lesson_count = lesson_count
        program.save(update_fields=["module_count", "lesson_count", "updated_at"])
        return program

    @staticmethod
    def refresh_module_lesson_count(module: Module) -> Module:
        count = Lesson.objects.filter(module=module, is_published=True).count()
        module.lesson_count = count
        module.save(update_fields=["lesson_count", "updated_at"])
        return module
