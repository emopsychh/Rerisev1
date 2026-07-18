from django.core.management import call_command
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.content.models import MaterialFile, MaterialGroup
from apps.partner.models import PartnerProfile
from tests.support import AuthStoreTestMixin


class ContentAPITestCase(AuthStoreTestMixin, TestCase):
    def setUp(self):
        self.client = APIClient()
        self.seed_store()
        call_command("seed_academy")
        call_command("seed_content")
        self.register_user("member@rerise.ai", first_name="Участник", last_name="Тест")
        self.login_user("member@rerise.ai")
        self.buy_tariff("rise")

    def test_home_returns_banners_and_programs_count(self):
        response = self.client.get("/api/v1/home")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data["data"]
        self.assertGreaterEqual(len(data["banners"]), 1)
        self.assertIn("image_url", data["banners"][0])
        self.assertEqual(data["ai_box_widget"]["is_available"], True)
        self.assertGreaterEqual(data["programs_count"], 3)

    def test_materials_catalog_filters_by_tariff(self):
        response = self.client.get("/api/v1/materials")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data["data"]
        self.assertEqual(data["stats"]["total_sections"], 5)

        titles = [
            group["title"]
            for category in data["categories"]
            for group in category["groups"]
        ]
        self.assertIn("Промпты", titles)
        self.assertIn("Партнёрские материалы", titles)
        self.assertNotIn("Flows", titles)
        self.assertNotIn("Чек-листы", titles)

    def test_materials_category_filter(self):
        response = self.client.get("/api/v1/materials?category=sales")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        categories = response.data["data"]["categories"]
        self.assertEqual(len(categories), 1)
        self.assertEqual(categories[0]["slug"], "sales")

    def test_material_group_detail_and_download(self):
        group = MaterialGroup.objects.get(title="Промпты")
        detail = self.client.get(f"/api/v1/materials/groups/{group.id}")
        self.assertEqual(detail.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(detail.data["data"]["files"]), 1)

        material_file = MaterialFile.objects.filter(group=group).first()
        download = self.client.get(f"/api/v1/materials/files/{material_file.id}/download")
        self.assertEqual(download.status_code, status.HTTP_302_FOUND)
        self.assertEqual(download["Location"], material_file.file_url)

    def test_locked_material_group_returns_403(self):
        group = MaterialGroup.objects.get(title="Чек-листы")
        response = self.client.get(f"/api/v1/materials/groups/{group.id}")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_chats_invite_locked_for_partner_1(self):
        response = self.client.get("/api/v1/chats")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data["data"]
        self.assertTrue(data["community_active"])
        self.assertEqual(len(data["chats"]), 5)
        self.assertIsNotNone(data.get("marketing_channel"))
        self.assertEqual(data["marketing_channel"]["title"], "Канал маркетинга")
        self.assertTrue(data["marketing_channel"]["is_accessible"])

        by_title = {chat["title"]: chat for chat in data["chats"]}
        self.assertTrue(by_title["Чат партнёров"]["is_accessible"])
        self.assertFalse(by_title["Чат лидеров"]["is_accessible"])
        self.assertEqual(by_title["Чат лидеров"]["access_requirement"], "Партнёр II и выше")
        self.assertIsNone(by_title["Чат лидеров"]["telegram_url"])
        self.assertNotIn("Канал маркетинга", by_title)

    def test_chats_invite_unlocked_after_rank_up(self):
        partner = PartnerProfile.objects.get(user__email="member@rerise.ai")
        partner.highest_rank = "partner_2"
        partner.current_rank = "partner_2"
        partner.save(update_fields=["highest_rank", "current_rank", "updated_at"])

        response = self.client.get("/api/v1/chats")
        leaders = next(
            chat for chat in response.data["data"]["chats"] if chat["title"] == "Чат лидеров"
        )
        self.assertTrue(leaders["is_accessible"])
        self.assertEqual(leaders["telegram_url"], "https://t.me/rerise_leaders")

    def test_unknown_required_tariff_denies_access(self):
        group = MaterialGroup.objects.get(title="Промпты")
        group.required_tariff = "not-a-real-tariff"
        group.save(update_fields=["required_tariff", "updated_at"])

        response = self.client.get(f"/api/v1/materials/groups/{group.id}")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        catalog = self.client.get("/api/v1/materials")
        titles = [
            item["title"]
            for category in catalog.data["data"]["categories"]
            for item in category["groups"]
        ]
        self.assertNotIn("Промпты", titles)

    def test_download_rejects_external_redirect(self):
        group = MaterialGroup.objects.get(title="Промпты")
        material_file = MaterialFile.objects.filter(group=group).first()
        material_file.file_url = "https://evil.example/steal"
        material_file.save(update_fields=["file_url", "updated_at"])

        response = self.client.get(f"/api/v1/materials/files/{material_file.id}/download")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"]["code"], "INVALID_FILE_URL")
