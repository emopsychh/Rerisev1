from rest_framework import status
from rest_framework.views import APIView

from apps.academy.access import load_user_access_context, user_has_program_access
from apps.academy.constants import FILTER_ALL, PROGRAM_FILTER_CHOICES
from apps.academy.models import UserProgress
from apps.academy.selectors import (
    filter_programs_for_user,
    get_lesson_for_user,
    get_program_by_slug,
    get_published_programs_queryset,
    serialize_lesson_detail,
    serialize_program_card,
    serialize_program_detail,
)
from apps.academy.serializers import LessonProgressUpdateSerializer
from apps.academy.services import AcademyAccessError, ProgressService
from core.pagination import StandardPagination
from core.responses import error_response, success_response


class ProgramListView(APIView):
    pagination_class = StandardPagination

    def get(self, request):
        filter_name = request.query_params.get("filter", FILTER_ALL)
        if filter_name not in PROGRAM_FILTER_CHOICES:
            filter_name = FILTER_ALL

        search = request.query_params.get("search")
        queryset = filter_programs_for_user(
            get_published_programs_queryset(),
            request.user,
            filter_name,
            search,
        )

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)

        progress_map = {
            progress.program_id: progress
            for progress in UserProgress.objects.filter(
                user=request.user,
                program_id__in=[program.id for program in page],
            )
        }
        access_context = load_user_access_context(request.user)

        data = [
            serialize_program_card(
                program,
                request.user,
                progress_map.get(program.id),
                access_context=access_context,
            )
            for program in page
        ]
        return paginator.get_paginated_response(data)


class ProgramDetailView(APIView):
    def get(self, request, slug: str):
        program = get_program_by_slug(slug)
        if not program:
            return error_response(
                "NOT_FOUND",
                "Программа не найдена",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        # Locked programs still return a card payload (no modules) so UI can show
        # «нужен тариф» instead of a bare 403 with an empty page.
        return success_response(serialize_program_detail(program, request.user))


class LessonDetailView(APIView):
    def get(self, request, lesson_id: int):
        lesson = get_lesson_for_user(lesson_id, request.user.pk)
        if not lesson:
            return error_response(
                "NOT_FOUND",
                "Урок не найден",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        if not user_has_program_access(request.user, lesson.module.program):
            return error_response(
                "FORBIDDEN",
                "Нет доступа к этому уроку",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        from apps.academy.models import LessonProgress

        lesson_progress = LessonProgress.objects.filter(
            user=request.user, lesson=lesson
        ).first()
        return success_response(serialize_lesson_detail(lesson, request.user, lesson_progress))


class LessonStartView(APIView):
    def post(self, request, lesson_id: int):
        lesson = get_lesson_for_user(lesson_id, request.user.pk)
        if not lesson:
            return error_response(
                "NOT_FOUND",
                "Урок не найден",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        try:
            progress = ProgressService.start_lesson(request.user, lesson)
        except AcademyAccessError as exc:
            return error_response(
                "FORBIDDEN",
                str(exc),
                status_code=status.HTTP_403_FORBIDDEN,
            )

        return success_response(
            {
                "lesson_id": lesson.id,
                "status": progress.status,
                "started_at": progress.started_at.isoformat().replace("+00:00", "Z"),
            }
        )


class LessonProgressView(APIView):
    def patch(self, request, lesson_id: int):
        lesson = get_lesson_for_user(lesson_id, request.user.pk)
        if not lesson:
            return error_response(
                "NOT_FOUND",
                "Урок не найден",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        serializer = LessonProgressUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            progress = ProgressService.update_video_position(
                request.user,
                lesson,
                serializer.validated_data["video_position_sec"],
            )
        except AcademyAccessError as exc:
            return error_response(
                "FORBIDDEN",
                str(exc),
                status_code=status.HTTP_403_FORBIDDEN,
            )

        return success_response(
            {
                "lesson_id": lesson.id,
                "video_position_sec": progress.video_position_sec,
            }
        )


class LessonCompleteView(APIView):
    def post(self, request, lesson_id: int):
        lesson = get_lesson_for_user(lesson_id, request.user.pk)
        if not lesson:
            return error_response(
                "NOT_FOUND",
                "Урок не найден",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        try:
            result = ProgressService.complete_lesson(request.user, lesson)
        except AcademyAccessError as exc:
            return error_response(
                "FORBIDDEN",
                str(exc),
                status_code=status.HTTP_403_FORBIDDEN,
            )

        return success_response(result)
