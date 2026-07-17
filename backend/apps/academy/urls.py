from django.urls import path

from apps.academy.views.programs import (
    LessonCompleteView,
    LessonDetailView,
    LessonProgressView,
    LessonStartView,
    ProgramDetailView,
    ProgramListView,
)

urlpatterns = [
    path("programs", ProgramListView.as_view(), name="program-list"),
    path("programs/<slug:slug>", ProgramDetailView.as_view(), name="program-detail"),
    path("lessons/<int:lesson_id>", LessonDetailView.as_view(), name="lesson-detail"),
    path("lessons/<int:lesson_id>/start", LessonStartView.as_view(), name="lesson-start"),
    path(
        "lessons/<int:lesson_id>/progress",
        LessonProgressView.as_view(),
        name="lesson-progress",
    ),
    path(
        "lessons/<int:lesson_id>/complete",
        LessonCompleteView.as_view(),
        name="lesson-complete",
    ),
]
