from django.core.management import call_command
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.academy.models import Lesson, LessonProgress, ModuleProgress, Program, UserProgress
from tests.support import AuthStoreTestMixin


class AcademyAPITestCase(AuthStoreTestMixin, TestCase):
    def setUp(self):
        self.client = APIClient()
        self.seed_store()
        call_command("seed_academy")
        self.register_user("student@rerise.ai", first_name="Студент", last_name="Тест")
        self.login_user("student@rerise.ai")
        self.buy_tariff("rise-pro")

    def test_program_list_shows_access_status(self):
        response = self.client.get("/api/v1/programs")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        programs = {item["slug"]: item for item in response.data["data"]}
        self.assertEqual(programs["gpt-new"]["access_status"], "owned")
        self.assertEqual(programs["ai-design"]["access_status"], "owned")
        self.assertEqual(programs["ai-video"]["access_status"], "locked")

    def test_program_detail_with_modules(self):
        response = self.client.get("/api/v1/programs/gpt-new")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data["data"]
        self.assertEqual(data["slug"], "gpt-new")
        self.assertEqual(data["module_count"], 6)
        self.assertEqual(data["lesson_count"], 21)
        self.assertEqual(len(data["modules"]), 6)

    def test_lesson_start_progress_complete_flow(self):
        program = Program.objects.get(slug="gpt-new")
        lesson = Lesson.objects.filter(module__program=program).order_by(
            "module__sort_order", "sort_order"
        ).first()

        start = self.client.post(f"/api/v1/lessons/{lesson.id}/start")
        self.assertEqual(start.status_code, status.HTTP_200_OK)
        self.assertEqual(start.data["data"]["status"], "in_progress")

        patch = self.client.patch(
            f"/api/v1/lessons/{lesson.id}/progress",
            {"video_position_sec": 142},
            format="json",
        )
        self.assertEqual(patch.status_code, status.HTTP_200_OK)
        self.assertEqual(patch.data["data"]["video_position_sec"], 142)

        complete = self.client.post(f"/api/v1/lessons/{lesson.id}/complete")
        self.assertEqual(complete.status_code, status.HTTP_200_OK)
        self.assertEqual(complete.data["data"]["status"], "completed")
        self.assertEqual(complete.data["data"]["program_progress"]["completed_lessons"], 1)
        self.assertGreater(complete.data["data"]["program_progress"]["percent"], 0)

        lesson_progress = LessonProgress.objects.get(user__email="student@rerise.ai", lesson=lesson)
        self.assertEqual(lesson_progress.status, "completed")
        self.assertEqual(lesson_progress.video_position_sec, 142)

        user_progress = UserProgress.objects.get(
            user__email="student@rerise.ai", program=program
        )
        self.assertEqual(user_progress.status, "in_progress")
        self.assertEqual(user_progress.completed_lessons, 1)

    def test_complete_intro_module_updates_completed_modules(self):
        program = Program.objects.get(slug="gpt-new")
        lesson = Lesson.objects.filter(module__program=program, module__is_intro=True).first()
        self.assertEqual(lesson.module.lesson_count, 1)

        complete = self.client.post(f"/api/v1/lessons/{lesson.id}/complete")
        self.assertEqual(complete.status_code, status.HTTP_200_OK)
        self.assertEqual(complete.data["data"]["module_progress"]["status"], "completed")
        self.assertEqual(complete.data["data"]["program_progress"]["completed_modules"], 1)

    def test_start_marks_current_module_in_detail(self):
        program = Program.objects.get(slug="gpt-new")
        lesson = Lesson.objects.filter(module__program=program).order_by(
            "module__sort_order", "sort_order"
        ).first()

        self.client.post(f"/api/v1/lessons/{lesson.id}/start")
        detail = self.client.get("/api/v1/programs/gpt-new")
        intro_module = detail.data["data"]["modules"][0]
        self.assertEqual(intro_module["progress"]["status"], "current")

        module_progress = ModuleProgress.objects.get(
            user__email="student@rerise.ai", module_id=intro_module["id"]
        )
        self.assertEqual(module_progress.status, "in_progress")

    def test_complete_updates_last_lesson_to_next(self):
        program = Program.objects.get(slug="gpt-new")
        lessons = list(
            Lesson.objects.filter(module__program=program).order_by(
                "module__sort_order", "sort_order"
            )[:2]
        )
        first, second = lessons

        self.client.post(f"/api/v1/lessons/{first.id}/complete")
        user_progress = UserProgress.objects.get(
            user__email="student@rerise.ai", program=program
        )
        self.assertEqual(user_progress.last_lesson_id, second.id)

    def test_locked_program_returns_empty_modules(self):
        response = self.client.get("/api/v1/programs/ai-video")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data["data"]
        self.assertEqual(data["access_status"], "locked")
        self.assertEqual(data["modules"], [])
        self.assertIsNone(data["progress"])

    def test_no_tariff_locks_all_programs(self):
        self.register_user("notier@rerise.ai", first_name="Без", last_name="Тарифа")
        self.login_user("notier@rerise.ai")
        listing = self.client.get("/api/v1/programs")
        self.assertEqual(listing.status_code, status.HTTP_200_OK)
        for item in listing.data["data"]:
            self.assertEqual(item["access_status"], "locked", item["slug"])

        detail = self.client.get("/api/v1/programs/gpt-new")
        self.assertEqual(detail.status_code, status.HTTP_200_OK)
        self.assertEqual(detail.data["data"]["access_status"], "locked")
        self.assertEqual(detail.data["data"]["modules"], [])

    def test_lesson_detail(self):
        lesson = Lesson.objects.filter(module__program__slug="gpt-new").first()
        response = self.client.get(f"/api/v1/lessons/{lesson.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data["data"]
        self.assertEqual(data["program"]["slug"], "gpt-new")
        self.assertIn("video", data)
        self.assertIn("resources", data)

    def test_filter_completed_programs(self):
        program = Program.objects.get(slug="gpt-new")
        lesson = Lesson.objects.filter(module__program=program).first()
        self.client.post(f"/api/v1/lessons/{lesson.id}/start")
        self.client.post(f"/api/v1/lessons/{lesson.id}/complete")

        response = self.client.get("/api/v1/programs?filter=owned")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        slugs = [item["slug"] for item in response.data["data"]]
        self.assertIn("gpt-new", slugs)
