from django.db.models import Prefetch, Q

from apps.academy.access import load_user_access_context, user_has_program_access
from apps.academy.constants import (
    ACCESS_COMPLETED,
    ACCESS_IN_PROGRESS,
    ACCESS_LOCKED,
    ACCESS_OWNED,
    FILTER_ALL,
    FILTER_AVAILABLE,
    FILTER_COMPLETED,
    FILTER_OWNED,
    STATUS_COMPLETED,
    STATUS_CURRENT,
    STATUS_IN_PROGRESS,
    STATUS_NOT_STARTED,
)
from apps.academy.models import (
    Lesson,
    LessonProgress,
    LessonResource,
    Module,
    ModuleProgress,
    Program,
    UserProgress,
)


def get_published_programs_queryset():
    return Program.objects.filter(is_published=True).order_by("sort_order", "title")


def get_program_by_slug(slug: str) -> Program | None:
    return (
        Program.objects.filter(slug=slug, is_published=True)
        .prefetch_related(
            Prefetch(
                "modules",
                queryset=Module.objects.filter(is_published=True)
                .prefetch_related(
                    Prefetch(
                        "lessons",
                        queryset=Lesson.objects.filter(is_published=True).order_by(
                            "sort_order"
                        ),
                    )
                )
                .order_by("sort_order"),
            )
        )
        .first()
    )


def get_lesson_for_user(lesson_id: int, user_id: int) -> Lesson | None:
    return (
        Lesson.objects.filter(
            pk=lesson_id,
            is_published=True,
            module__is_published=True,
            module__program__is_published=True,
        )
        .select_related("module__program")
        .prefetch_related(
            Prefetch(
                "resources",
                queryset=LessonResource.objects.order_by("sort_order", "id"),
            )
        )
        .first()
    )


def _progress_maps(user_id: int, program_ids: list[int]) -> dict[int, UserProgress]:
    return {
        progress.program_id: progress
        for progress in UserProgress.objects.filter(
            user_id=user_id, program_id__in=program_ids
        )
    }


def _lesson_progress_map(user_id: int, lesson_ids: list[int]) -> dict[int, LessonProgress]:
    return {
        progress.lesson_id: progress
        for progress in LessonProgress.objects.filter(
            user_id=user_id, lesson_id__in=lesson_ids
        )
    }


def _module_progress_map(user_id: int, module_ids: list[int]) -> dict[int, ModuleProgress]:
    return {
        progress.module_id: progress
        for progress in ModuleProgress.objects.filter(
            user_id=user_id, module_id__in=module_ids
        )
    }


def filter_programs_for_user(queryset, user, filter_name: str, search: str | None):
    if search:
        queryset = queryset.filter(
            Q(title__icontains=search) | Q(description__icontains=search)
        )

    if filter_name == FILTER_ALL:
        return queryset

    program_ids = list(queryset.values_list("id", flat=True))
    progress_by_program = _progress_maps(user.pk, program_ids)
    access_context = load_user_access_context(user)

    filtered_ids = []
    for program in queryset:
        has_access = user_has_program_access(user, program, access_context=access_context)
        progress = progress_by_program.get(program.id)

        if filter_name == FILTER_OWNED:
            if has_access and (not progress or progress.status != STATUS_COMPLETED):
                filtered_ids.append(program.id)
        elif filter_name == FILTER_AVAILABLE:
            if has_access:
                filtered_ids.append(program.id)
        elif filter_name == FILTER_COMPLETED:
            if progress and progress.status == STATUS_COMPLETED:
                filtered_ids.append(program.id)

    return queryset.filter(id__in=filtered_ids)


def resolve_access_status(
    user,
    program: Program,
    progress: UserProgress | None,
    *,
    access_context: dict | None = None,
) -> str:
    if not user_has_program_access(user, program, access_context=access_context):
        return ACCESS_LOCKED
    if progress is None or progress.status == STATUS_NOT_STARTED:
        return ACCESS_OWNED
    if progress.status == STATUS_COMPLETED:
        return ACCESS_COMPLETED
    return ACCESS_IN_PROGRESS


def resolve_action(access_status: str, progress: UserProgress | None) -> str:
    from apps.academy.constants import ACTION_CONTINUE, ACTION_DETAILS, ACTION_OPEN

    if access_status == ACCESS_LOCKED:
        return ACTION_DETAILS
    if progress and progress.status in (STATUS_IN_PROGRESS, STATUS_COMPLETED):
        if progress.status == STATUS_IN_PROGRESS:
            return ACTION_CONTINUE
    return ACTION_OPEN


def serialize_program_card(
    program: Program,
    user,
    progress: UserProgress | None,
    *,
    access_context: dict | None = None,
) -> dict:
    access_status = resolve_access_status(user, program, progress, access_context=access_context)
    action = resolve_action(access_status, progress)

    data = {
        "id": program.id,
        "slug": program.slug,
        "title": program.title,
        "description": program.description,
        "lesson_count": program.lesson_count,
        "module_count": program.module_count,
        "icon": program.icon,
        "tags": program.tags or [],
        "access_status": access_status,
        "action": action,
    }

    if access_status == ACCESS_LOCKED:
        data["progress"] = None
    else:
        data["progress"] = {
            "status": progress.status if progress else STATUS_NOT_STARTED,
            "completed_lessons": progress.completed_lessons if progress else 0,
            "percent": progress.progress_percent if progress else 0,
        }

    return data


def serialize_lesson_brief(lesson: Lesson, lesson_progress: LessonProgress | None) -> dict:
    status = lesson_progress.status if lesson_progress else STATUS_NOT_STARTED
    return {
        "id": lesson.id,
        "order": lesson.sort_order,
        "title": lesson.title,
        "duration_minutes": lesson.duration_minutes,
        "type": lesson.lesson_type,
        "status": status,
    }


def serialize_module_brief(
    module: Module,
    module_progress: ModuleProgress | None,
    lesson_progresses: dict[int, LessonProgress],
    *,
    mark_current: bool = False,
) -> dict:
    if mark_current:
        status = STATUS_CURRENT
    else:
        status = module_progress.status if module_progress else STATUS_NOT_STARTED

    completed = module_progress.completed_lessons if module_progress else 0
    return {
        "id": module.id,
        "order": module.sort_order,
        "title": module.title,
        "description": module.description,
        "is_intro": module.is_intro,
        "lesson_count": module.lesson_count,
        "progress": {
            "completed_lessons": completed,
            "status": status,
        },
        "lessons": [
            serialize_lesson_brief(lesson, lesson_progresses.get(lesson.id))
            for lesson in module.lessons.all()
        ],
    }


def serialize_program_detail(program: Program, user) -> dict:
    user_progress = UserProgress.objects.filter(user=user, program=program).first()

    lesson_ids = []
    module_ids = []
    for module in program.modules.all():
        module_ids.append(module.id)
        lesson_ids.extend(lesson.id for lesson in module.lessons.all())

    lesson_progresses = _lesson_progress_map(user.pk, lesson_ids)
    module_progresses = _module_progress_map(user.pk, module_ids)

    last_lesson_payload = None
    if user_progress and user_progress.last_lesson_id:
        lesson = user_progress.last_lesson
        last_lesson_payload = {
            "id": lesson.id,
            "title": lesson.title,
            "module_title": lesson.module.title,
            "duration_minutes": lesson.duration_minutes,
        }

    current_module_id = _find_current_module_id(program, lesson_progresses)

    modules_payload = []
    for module in program.modules.all():
        modules_payload.append(
            serialize_module_brief(
                module,
                module_progresses.get(module.id),
                lesson_progresses,
                mark_current=module.id == current_module_id,
            )
        )

    progress_payload = None
    if user_progress:
        progress_payload = {
            "percent": user_progress.progress_percent,
            "completed_lessons": user_progress.completed_lessons,
            "completed_modules": user_progress.completed_modules,
            "status": user_progress.status,
            "last_lesson": last_lesson_payload,
        }

    return {
        "id": program.id,
        "slug": program.slug,
        "title": program.title,
        "description": program.description,
        "lesson_count": program.lesson_count,
        "module_count": program.module_count,
        "progress": progress_payload,
        "modules": modules_payload,
    }


def _find_current_module_id(program: Program, lesson_progresses: dict[int, LessonProgress]) -> int | None:
    for module in program.modules.all():
        for lesson in module.lessons.all():
            progress = lesson_progresses.get(lesson.id)
            if not progress or progress.status != STATUS_COMPLETED:
                return module.id
    return None


def serialize_lesson_detail(lesson: Lesson, user, lesson_progress: LessonProgress | None) -> dict:
    resources = []
    for resource in lesson.resources.all():
        item = {
            "type": resource.resource_type,
            "title": resource.title,
            "file_url": resource.file_url,
        }
        if resource.resource_type == "practice" and lesson.ibox_scenario_id:
            item["ibox_scenario_id"] = lesson.ibox_scenario_id
        resources.append(item)

    video = None
    video_url = lesson.resolved_video_url
    if video_url:
        video = {
            "url": video_url,
            "quality": lesson.video_quality or "HD",
        }

    progress_status = lesson_progress.status if lesson_progress else STATUS_NOT_STARTED
    video_position = lesson_progress.video_position_sec if lesson_progress else 0

    return {
        "id": lesson.id,
        "title": lesson.title,
        "description": lesson.description,
        "result_description": lesson.result_description,
        "type": lesson.lesson_type,
        "duration_minutes": lesson.duration_minutes,
        "video": video,
        "resources": resources,
        "program": {
            "slug": lesson.program.slug,
            "title": lesson.program.title,
        },
        "module": {
            "id": lesson.module_id,
            "title": lesson.module.title,
        },
        "progress": {
            "status": progress_status,
            "video_position_sec": video_position,
        },
    }


def find_next_lesson(lesson: Lesson) -> Lesson | None:
    program = lesson.module.program
    lessons = (
        Lesson.objects.filter(
            module__program=program,
            is_published=True,
            module__is_published=True,
        )
        .select_related("module")
        .order_by("module__sort_order", "sort_order")
    )

    found = False
    for candidate in lessons:
        if found:
            return candidate
        if candidate.id == lesson.id:
            found = True
    return None
